# Project Coding Harness for Claude Code

Codex용 Project Coding Harness를 Claude Code 플러그인으로 포팅한 버전입니다. 프로젝트 구조와 검증 방법을 Markdown으로 기억하고, 사용자가 승인한 결정만 저장하며, 설정한 횟수 안에서 코드 검수를 기록합니다. 별도 프레임워크나 LLM 서버, API 키, Python 패키지는 필요하지 않습니다.

## 준비

- 플러그인을 지원하는 Claude Code. 이 패키지의 manifest 검증은 로컬 Claude Code **2.1.278**에서 수행합니다. 해당 버전의 validator는 MCP 항목 상세 검증을 지원하지 않아 별도 stdio 테스트도 제공합니다.
- PATH에서 실행되는 **Python 3.10 이상** (`python --version`). Windows에서는 Store 별칭이 아닌 실제 Python 실행 파일이 필요합니다. `python` 대신 다른 실행 명령이 필요한 환경은 `.mcp.json`의 `command`를 실제 interpreter로 바꾸세요.
- 대시보드를 열 웹브라우저. Claude Code의 현재 프로젝트에 읽기/쓰기 권한이 필요합니다.

## 바로 실행

개발할 프로젝트 디렉터리에서 실행합니다. 플러그인 디렉터리와 개발할 프로젝트 디렉터리는 서로 다른 역할입니다.

```powershell
cd C:/path/to/your-project
claude --plugin-dir C:/path/to/Project-Coding-Harness/plugins/claude-project-coding-harness
```

이 명령은 해당 세션에서 플러그인을 로드합니다. 기존 Claude 세션에서는 변경 후 `/reload-plugins`를 사용하세요. `/mcp`에서 `plugin:project-coding-harness:harness` 서버의 연결 상태를 확인할 수 있습니다. 호스트가 표시하는 MCP 연결·도구 권한 안내를 따라주세요.

수동으로 시작하려면 Claude Code 대화에 입력하세요.

```text
/project-coding-harness:project-coding-harness 하네스 설정 페이지를 열어줘.
/project-coding-harness:project-coding-harness 이 프로젝트를 분석하고 기억해줘.
/project-coding-harness:project-coding-harness 이번 변경을 적대적으로 검수해줘.
```

자연어 요청도 지원합니다. 본격적인 코딩에서는 skill description에 따라 Claude가 자동으로 선택할 수 있습니다. 자동 선택은 모델의 판단이며 모든 턴에 강제되는 hook은 아닙니다. 분석과 영구 기억 갱신은 명시적으로 요청하거나 설정 페이지에서 선택해야 시작합니다. “이번 대화에서는 끄기”는 대화에만 적용하고, “이 프로젝트에서는 요청할 때만 사용하기”는 프로젝트 설정으로 저장합니다.

## GitHub 마켓플레이스로 설치

세션 로딩 대신 지속 설치를 원할 때 아래 두 줄을 터미널에 붙여넣으세요. 이 명령은 사용자 플러그인 설정에 저장소를 등록하고 설치합니다.

```powershell
claude plugin marketplace add thgus851/Project-Coding-Harness
claude plugin install project-coding-harness@project-coding-harness-claude --scope user
```

현재 프로젝트에서만 설치하려면 `--scope project` 또는 `--scope local`을 선택하세요. `project` 범위는 팀에 공유하는 프로젝트 설정이고 `local` 범위는 개인 프로젝트 설정입니다. GitHub marketplace는 각 사용자가 등록하고 설치합니다. 로컬 checkout으로 시험하려면 저장소 루트에서 `claude plugin marketplace add .`를 사용할 수도 있습니다.

## 동작과 저장 위치

MCP 도구는 `mcp__plugin_project-coding-harness_harness__harness_<action>` 이름으로 제공됩니다. 모든 호출은 실제 작업 프로젝트의 절대 `project_root`를 요구합니다. `preferences`와 `status`는 읽기만 하며, 플러그인을 로드하거나 상태를 보는 것만으로 `.coding-harness`를 생성하지 않습니다.

설정과 기억은 해당 프로젝트의 `.coding-harness/`에 저장합니다. `memory.md`는 분석과 승인된 결정, `state.json`은 설정·대기 요청·제안·검수 기록, `history/`는 이전 기억을 보관합니다. Claude 내장 auto memory, `CLAUDE.md`, `~/.claude` 설정은 수정하지 않습니다. Codex 버전과 같은 storage schema를 사용하므로 기존 기억을 읽을 수 있지만, 같은 프로젝트를 두 호스트에서 동시에 편집하지 않는 편이 좋습니다.

`harness_dashboard`와 `harness_panel`은 `dashboard_url`을 반환합니다. Claude가 제공한 `http://127.0.0.1:...` 링크를 브라우저에서 여세요. 서버는 loopback에만 바인딩되고 임의 token URL과 Origin 검사를 사용합니다. MCP 프로세스가 끝나면 페이지도 사용할 수 없습니다. 페이지에서 분석 버튼을 누르면 대기 요청이 저장되며, 표시된 slash 요청을 **현재 프로젝트의 Claude Code 대화**에 복사해야 AI 분석이 진행됩니다.

검수 도구는 횟수와 근거를 기록하며 AI를 직접 호출하거나 테스트를 실행하지 않습니다. Claude가 코드를 검토하고 합의된 검증을 수행합니다. 독립 검수가 허용되고 subagent 도구가 있으면 별도 reviewer에 맡기고, 없으면 별도 self-review임을 밝힙니다. 설정한 최대 횟수를 넘겨 새 run으로 우회하지 않습니다. 기억 제안은 사용자 동의 전까지 활성 기억으로 취급하지 않습니다.

## 검증과 CLI fallback

저장소 루트에서 실행하세요.

```powershell
claude plugin validate ./plugins/claude-project-coding-harness/.claude-plugin/plugin.json --strict
claude plugin validate . --strict
python -B -m unittest discover -s ./plugins/claude-project-coding-harness/tests -v
```

plugin manifest는 이 플러그인 폴더에, marketplace manifest는 저장소 루트 `.claude-plugin/marketplace.json`에 있습니다. marketplace 검증은 저장소 루트 경로를 전달하세요. 테스트는 임시 프로젝트에서 MCP stdio 초기화, 도구 호출, 브라우저 경계, 분석 요청과 동의 규칙을 검사하고 임시 파일을 정리합니다. 실제 Claude 세션의 skill 선택, 모델 검수 품질, 브라우저 렌더링은 별도 확인이 필요합니다.

MCP를 사용할 수 없으면 저장소 루트에서 CLI로 호출할 수 있습니다. `--project`는 개발할 프로젝트의 실제 절대 경로로 바꾸세요.

```powershell
python ./plugins/claude-project-coding-harness/scripts/harness.py call preferences --project C:/path/to/your-project
python ./plugins/claude-project-coding-harness/scripts/harness.py dashboard --project C:/path/to/your-project
```

쓰기 action payload는 UTF-8 JSON 파일을 만들고 `--payload C:/path/to/payload.json`으로 전달하거나 stdin과 `--payload -`를 사용하세요. 대시보드 CLI는 종료할 때까지 실행됩니다. 코드 변경이 끝났다는 이유만으로 Git commit, push, 배포 또는 외부 메시지를 수행하지 않습니다.

## 출처와 구조

이 thgus851 배포본의 원본은 [ToolStorage/Project-Coding-Harness](https://github.com/ToolStorage/Project-Coding-Harness)의 로컬 Codex 패키지 `0.1.0+codex.20260928084243`입니다. 이 저장소 루트의 `LICENSE`가 MIT 라이선스와 Copyright (c) 2026 ToolStorage 고지를 제공합니다. 재배포 시 이 고지를 유지하세요.

`scripts/store.py`의 저장·동의·동시성 정책을 유지하고, 분석 요청 문구를 Claude slash 명령으로 변경했습니다. `scripts/harness.py`의 stdio MCP와 loopback 서버를 재사용하되 Codex MCP App metadata/resource를 제거했습니다. `ui/`는 일반 브라우저 전용이며 `skills/`는 Claude 도구 namespace와 독립 subagent 검수 안내를 포함합니다.

구현 기준: [plugin reference](https://code.claude.com/docs/en/plugins-reference), [MCP components](https://code.claude.com/docs/en/plugins/components#mcp-servers), [plugin creation](https://code.claude.com/docs/en/plugins/create), [CLI reference](https://code.claude.com/docs/en/plugins/cli-reference), [skills](https://code.claude.com/docs/en/skills).

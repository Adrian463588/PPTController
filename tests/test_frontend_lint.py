import subprocess
from pathlib import Path

def test_javascript_syntax_and_runtime_integrity():
    """Validates that frontend JavaScript files have valid syntax and zero ReferenceErrors."""
    project_root = Path(__file__).resolve().parent.parent
    app_js = project_root / "web" / "js" / "app.js"
    ws_js = project_root / "web" / "js" / "websocket.js"

    assert app_js.exists(), "web/js/app.js must exist"
    assert ws_js.exists(), "web/js/websocket.js must exist"

    # 1. Syntax check via node -c
    res_syntax_ws = subprocess.run(["node", "-c", str(ws_js)], capture_output=True, text=True)
    assert res_syntax_ws.returncode == 0, f"websocket.js syntax error: {res_syntax_ws.stderr}"

    res_syntax_app = subprocess.run(["node", "-c", str(app_js)], capture_output=True, text=True)
    assert res_syntax_app.returncode == 0, f"app.js syntax error: {res_syntax_app.stderr}"

    # 2. Runtime execution simulation with DOM mock to catch undeclared variables
    eval_script = """
    const fs = require('fs');
    const wsCode = fs.readFileSync(process.argv[1], 'utf8');
    const appCode = fs.readFileSync(process.argv[2], 'utf8');

    const mockEl = {
      addEventListener: () => {},
      removeEventListener: () => {},
      classList: { add: () => {}, remove: () => {}, toggle: () => {} },
      style: {},
      getAttribute: () => 'c',
      getBoundingClientRect: () => ({ left: 0, top: 0, width: 300, height: 300 })
    };

    const sandbox = {
      document: {
        addEventListener: (ev, fn) => fn(),
        getElementById: () => mockEl,
        querySelectorAll: () => [mockEl],
        documentElement: mockEl
      },
      window: {
        addEventListener: () => {},
        removeEventListener: () => {},
        location: { protocol: 'http:', host: 'localhost:8765' }
      },
      WebSocket: class MockWS { constructor() {} send() {} close() {} },
      navigator: { vibrate: () => true },
      Date, Math, setInterval, clearInterval, setTimeout, clearTimeout, console
    };

    const vm = require('vm');
    const ctx = vm.createContext(sandbox);
    vm.runInContext(wsCode, ctx);
    vm.runInContext(appCode, ctx);
    """

    res_eval = subprocess.run(
        ["node", "-e", eval_script, str(ws_js), str(app_js)],
        capture_output=True,
        text=True
    )
    assert res_eval.returncode == 0, f"JavaScript runtime evaluation failed: {res_eval.stderr}"

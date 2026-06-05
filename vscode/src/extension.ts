import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'detect-ai.scanFile';
    context.subscriptions.push(statusBarItem);

    const scanFile = vscode.commands.registerCommand('detect-ai.scanFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }
        const doc = editor.document;
        const result = await runDetection(doc.fileName, doc.getText());
        showResultPanel(result);
    });

    const scanSelection = vscode.commands.registerCommand('detect-ai.scanSelection', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        const selection = editor.selection;
        const text = editor.document.getText(selection);
        if (!text.trim()) {
            vscode.window.showWarningMessage('No selection');
            return;
        }
        const result = await runDetection('selection', text);
        showResultPanel(result);
    });

    const scanWorkspace = vscode.commands.registerCommand('detect-ai.scanWorkspace', async () => {
        const folders = vscode.workspace.workspaceFolders;
        if (!folders) {
            vscode.window.showWarningMessage('No workspace open');
            return;
        }
        const result = await runDetection(folders[0].uri.fsPath, '', true);
        showResultPanel(result);
    });

    context.subscriptions.push(scanFile, scanSelection, scanWorkspace);

    // Auto-scan on save
    vscode.workspace.onDidSaveTextDocument(async (doc) => {
        const config = vscode.workspace.getConfiguration('detect-ai');
        if (config.get<boolean>('showInStatusBar')) {
            const result = await runDetection(doc.fileName, doc.getText());
            updateStatusBar(result);
        }
    });
}

async function runDetection(filePath: string, source: string, isDir = false): Promise<any> {
    return new Promise((resolve, reject) => {
        const python = 'python';
        let args: string[];
        if (isDir) {
            args = ['-m', 'detect_ai.cli', 'scan', filePath, '-r', '-f', 'json'];
        } else {
            const ext = path.extname(filePath);
            const tmpFile = path.join(require('os').tmpdir(), `detect_ai_${Date.now()}${ext || '.py'}`);
            require('fs').writeFileSync(tmpFile, source);
            args = ['-m', 'detect_ai.cli', 'scan', tmpFile, '-f', 'json'];
        }
        cp.execFile(python, args, { timeout: 30000 }, (err, stdout) => {
            try {
                const data = JSON.parse(stdout);
                resolve(data);
            } catch {
                resolve({ error: stdout || err?.message });
            }
        });
    });
}

function updateStatusBar(result: any) {
    if (!statusBarItem) return;
    const score = result.overall_score ?? result.reports?.[0]?.overall_score ?? 0;
    const verdict = result.verdict ?? result.reports?.[0]?.verdict ?? 'unknown';
    const icon = score > 80 ? '$(warning)' : score > 50 ? '$(info)' : '$(check)';
    statusBarItem.text = `${icon} AI: ${score.toFixed(0)}`;
    statusBarItem.tooltip = `Verdict: ${verdict}\nScore: ${score}`;
    statusBarItem.show();
}

function showResultPanel(result: any) {
    const panel = vscode.window.createWebviewPanel(
        'detectAiResult',
        'AI Detection Result',
        vscode.ViewColumn.Two,
        { enableScripts: true }
    );

    const score = result.overall_score ?? result.reports?.[0]?.overall_score ?? 0;
    const verdict = result.verdict ?? result.reports?.[0]?.verdict ?? 'unknown';
    const rules = result.results ?? result.reports?.[0]?.results ?? [];

    const color = score > 80 ? '#e74c3c' : score > 50 ? '#f39c12' : '#2ecc71';
    const bar = (val: number) => `
        <div style="background:#334155;height:8px;border-radius:4px;overflow:hidden;margin:4px 0;">
            <div style="width:${val}%;background:${val > 70 ? '#e74c3c' : val > 40 ? '#f39c12' : '#2ecc71'};height:100%;"></div>
        </div>`;

    const rows = rules.map((r: any) => `
        <tr>
            <td style="padding:6px 12px;color:#94a3b8;font-size:13px;">${r.rule_name}</td>
            <td style="padding:6px 12px;width:200px;">${bar(r.score)}</td>
            <td style="padding:6px 12px;font-weight:600;color:${r.score > 70 ? '#e74c3c' : r.score > 40 ? '#f39c12' : '#2ecc71'};font-size:13px;">${r.score.toFixed(1)}</td>
        </tr>
    `).join('');

    panel.webview.html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background:#0f172a; color:#e2e8f0; padding:24px; }
        .score { font-size:64px; font-weight:800; color:${color}; }
        .verdict { display:inline-block; background:${color}22; color:${color}; border:1px solid ${color}44; border-radius:12px; padding:6px 16px; font-size:14px; font-weight:600; margin-top:12px; }
        table { width:100%; border-collapse:collapse; margin-top:20px; }
        th { text-align:left; color:#64748b; font-size:12px; padding:8px 12px; border-bottom:1px solid #334155; }
    </style>
</head>
<body>
    <div style="text-align:center;margin-bottom:32px;">
        <div class="score">${score.toFixed(1)}</div>
        <div style="color:#64748b;font-size:14px;">/ 100 AI Score</div>
        <div class="verdict">${verdict.toUpperCase()}</div>
    </div>
    <table>
        <thead><tr><th>Rule</th><th>Score</th><th>Value</th></tr></thead>
        <tbody>${rows}</tbody>
    </table>
</body>
</html>`;
}

export function deactivate() {
    if (statusBarItem) {
        statusBarItem.dispose();
    }
}

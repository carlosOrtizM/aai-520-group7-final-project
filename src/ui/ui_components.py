"""FastHTML/MonsterUI components for the agent advisor UI.

Components only — no routing, no inter-service calls, no business
logic. The @rt handlers in app.py compose these into responses.
"""

from fasthtml.common import *  # noqa: F401,F403
from monsterui.all import *  # noqa: F401,F403


USD_BRAND_CSS = Style("""
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --usd-founders: #003b70;
        --usd-immaculata: #0074c8;
        --usd-torero: #75bee9;
        --bg-primary: #0f172a;
        --bg-surface: #1e293b;
        --bg-card: #ffffff;
        --accent: #3b82f6;
        --accent-hover: #2563eb;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --text-primary: #0f172a;
        --text-secondary: #64748b;
        --text-muted: #94a3b8;
        --border: #e2e8f0;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
        --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
        --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.06);
    }

    * { box-sizing: border-box; }
    body { margin: 0; padding: 0; font-family: 'Inter', -apple-system, sans-serif; }
    .uk-container, .uk-section { max-width: 100% !important; width: 100% !important; }

    /* --- Launcher --- */
    .launcher-bg {
        min-height: 100vh;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #0074c8 100%);
        display: flex; align-items: center; justify-content: center;
        position: relative; overflow: hidden;
    }
    .launcher-bg::before {
        content: '';
        position: absolute; inset: 0;
        background: radial-gradient(circle at 30% 20%, rgba(59,130,246,0.15) 0%, transparent 50%),
                    radial-gradient(circle at 70% 80%, rgba(117,190,233,0.1) 0%, transparent 50%);
    }
    .launcher-card {
        position: relative; z-index: 1;
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 24px; padding: 60px 48px;
        text-align: center; max-width: 480px; width: 90%;
        box-shadow: 0 25px 50px rgba(0,0,0,0.25);
    }
    .launcher-icon {
        width: 72px; height: 72px; margin: 0 auto 24px;
        background: linear-gradient(135deg, var(--accent) 0%, var(--usd-torero) 100%);
        border-radius: 18px; display: flex; align-items: center; justify-content: center;
        box-shadow: 0 8px 24px rgba(59,130,246,0.3);
    }
    .launcher-icon svg { width: 36px; height: 36px; }
    .launcher-title {
        font-size: 32px; font-weight: 700; color: white;
        margin: 0 0 8px; letter-spacing: -0.5px;
    }
    .launcher-sub {
        font-size: 15px; color: rgba(255,255,255,0.6);
        margin: 0 0 40px; line-height: 1.5;
    }
    .launcher-btn {
        display: inline-flex; align-items: center; gap: 8px;
        background: linear-gradient(135deg, var(--accent), var(--accent-hover));
        color: white !important; font-weight: 600; font-size: 15px;
        padding: 14px 36px; border-radius: 12px; border: none;
        cursor: pointer; text-decoration: none !important;
        box-shadow: 0 4px 12px rgba(59,130,246,0.4);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .launcher-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59,130,246,0.5);
    }
    .launcher-badges {
        display: flex; gap: 12px; justify-content: center;
        margin-top: 32px; flex-wrap: wrap;
    }
    .launcher-badge {
        font-size: 11px; color: rgba(255,255,255,0.5);
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 6px 14px; border-radius: 100px;
    }

    /* --- Chat layout --- */
    .chat-layout { display: flex; height: 100vh; background: #f8fafc; }

    .chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

    .chat-header {
        padding: 20px 28px;
        background: white;
        border-bottom: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
    }
    .chat-header-title {
        font-size: 18px; font-weight: 700; color: var(--text-primary);
        margin: 0 0 2px; display: flex; align-items: center; gap: 10px;
    }
    .chat-header-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: var(--success); display: inline-block;
        box-shadow: 0 0 6px rgba(16,185,129,0.4);
    }
    .chat-header-sub {
        font-size: 13px; color: var(--text-muted); margin: 0;
    }

    .chat-thread {
        flex: 1; overflow-y: auto; padding: 24px 28px;
        background: #f8fafc;
    }

    .chat-input-bar {
        padding: 16px 28px 20px;
        background: white;
        border-top: 1px solid var(--border);
        box-shadow: 0 -2px 8px rgba(0,0,0,0.03);
    }
    .chat-input-row {
        display: flex; gap: 10px; align-items: center;
        background: #f1f5f9; border-radius: 14px;
        padding: 6px 6px 6px 18px;
        border: 2px solid transparent;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .chat-input-row:focus-within {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
        background: white;
    }
    .chat-input {
        flex: 1; border: none !important; background: transparent !important;
        font-size: 14px; padding: 10px 0 !important; outline: none !important;
        font-family: 'Inter', sans-serif; color: var(--text-primary);
        box-shadow: none !important;
    }
    .chat-input::placeholder { color: var(--text-muted); }
    .chat-send-btn {
        background: linear-gradient(135deg, var(--accent), var(--accent-hover)) !important;
        color: white !important; border: none !important;
        border-radius: 10px !important; padding: 10px 20px !important;
        font-weight: 600 !important; font-size: 13px !important;
        cursor: pointer; transition: transform 0.15s, box-shadow 0.15s;
        box-shadow: 0 2px 8px rgba(59,130,246,0.3);
    }
    .chat-send-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59,130,246,0.4);
    }

    /* --- Assessment CTA button (replaces chat input) --- */
    .assessment-btn-wrap {
        display: flex; justify-content: center;
    }
    .assessment-btn {
        display: flex; align-items: center; gap: 14px;
        width: 100%; max-width: 520px;
        padding: 16px 24px;
        background: linear-gradient(135deg, var(--usd-founders), var(--usd-immaculata)) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        cursor: pointer;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 6px 18px rgba(0,59,112,0.32);
        transition: transform 0.15s, box-shadow 0.2s;
    }
    .assessment-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(0,59,112,0.4);
    }
    .assessment-btn:disabled,
    .htmx-request .assessment-btn,
    .htmx-request.assessment-btn {
        opacity: 0.65;
        cursor: wait;
        transform: none;
    }
    .assessment-btn-icon {
        width: 44px; height: 44px; border-radius: 12px;
        background: rgba(255,255,255,0.15);
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }
    .assessment-btn-text {
        display: flex; flex-direction: column; align-items: flex-start;
        flex: 1; gap: 2px;
    }
    .assessment-btn-label {
        font-size: 15px; font-weight: 700; letter-spacing: -0.2px;
    }
    .assessment-btn-sub {
        font-size: 11px; opacity: 0.82; font-weight: 400;
    }
    .assessment-btn-arrow { opacity: 0.9; }

    /* --- Assessment output placeholder --- */
    .assessment-placeholder {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; gap: 12px;
        height: 100%; min-height: 240px;
        color: var(--text-muted); text-align: center; padding: 24px;
    }
    .assessment-placeholder-icon {
        width: 56px; height: 56px; border-radius: 14px;
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        display: flex; align-items: center; justify-content: center;
        color: var(--accent);
    }
    .assessment-placeholder-title {
        font-size: 15px; font-weight: 600; color: var(--text-primary); margin: 0;
    }
    .assessment-placeholder-sub {
        font-size: 13px; color: var(--text-muted); margin: 0; max-width: 360px;
    }

    /* --- Assessment card --- */
    .assessment-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 24px 28px;
        margin: 0 auto; max-width: 760px;
        box-shadow: var(--shadow-lg);
        animation: slideUp 0.35s ease;
    }
    .assessment-header {
        display: flex; align-items: center; justify-content: space-between;
        gap: 12px; margin-bottom: 12px;
    }
    .assessment-title {
        font-size: 22px; font-weight: 700; color: var(--text-primary);
        margin: 0; letter-spacing: -0.3px;
    }
    .outlook-badge {
        font-size: 11px; font-weight: 700; padding: 6px 14px;
        border-radius: 100px; text-transform: uppercase; letter-spacing: 0.6px;
    }
    .outlook-bullish { background: #ecfdf5; color: #059669; }
    .outlook-neutral { background: #f1f5f9; color: #475569; }
    .outlook-bearish { background: #fef2f2; color: #dc2626; }

    .assessment-thesis {
        font-size: 15px; font-weight: 500; color: var(--text-primary);
        line-height: 1.55; margin: 0 0 20px;
        padding: 14px 16px;
        background: #f8fafc;
        border-left: 3px solid var(--accent);
        border-radius: 8px;
    }
    .assessment-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
        margin-bottom: 20px;
    }
    .assessment-column {
        background: #fafbfc;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 14px 16px;
    }
    .assessment-column-bull { border-top: 3px solid #10b981; }
    .assessment-column-bear { border-top: 3px solid #ef4444; }
    .assessment-section-title {
        font-size: 11px; font-weight: 700; color: var(--text-secondary);
        text-transform: uppercase; letter-spacing: 0.6px;
        margin: 0 0 10px;
    }
    .assessment-list {
        margin: 0; padding-left: 18px;
        font-size: 13px; color: var(--text-primary); line-height: 1.55;
    }
    .assessment-list li { margin: 4px 0; }
    .assessment-block {
        background: #fafbfc;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .assessment-block-catalysts { border-top: 3px solid #f59e0b; }
    .assessment-block-risks { border-top: 3px solid #8b5cf6; }
    .assessment-empty {
        font-size: 12px; color: var(--text-muted); margin: 0;
    }
    .assessment-query {
        margin-top: 18px; padding-top: 14px;
        border-top: 1px dashed var(--border);
        font-size: 11px; color: var(--text-muted);
        display: flex; gap: 8px; flex-wrap: wrap;
    }
    .assessment-query-label { font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .assessment-query-text { font-style: italic; color: var(--text-secondary); }

    @media (max-width: 720px) {
        .assessment-grid { grid-template-columns: 1fr; }
    }

    /* --- Sidebar --- */
    .tools-sidebar {
        width: 360px; background: white;
        border-left: 1px solid var(--border);
        display: flex; flex-direction: column;
        box-shadow: -4px 0 12px rgba(0,0,0,0.03);
    }
    .sidebar-header {
        padding: 20px 24px;
        border-bottom: 1px solid var(--border);
    }
    .sidebar-header h4 {
        font-size: 14px; font-weight: 700; color: var(--text-primary);
        margin: 0; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .sidebar-body {
        flex: 1; overflow-y: auto; padding: 16px 20px;
    }

    .tool-btn {
        width: 100%; padding: 14px 16px;
        background: #f8fafc !important; color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important; margin-bottom: 8px;
        font-weight: 500 !important; font-size: 13px !important;
        cursor: pointer; transition: all 0.2s;
        display: flex !important; align-items: center; gap: 10px;
        text-align: left !important;
    }
    .tool-btn:hover {
        background: #f1f5f9 !important;
        border-color: var(--accent) !important;
        box-shadow: 0 2px 8px rgba(59,130,246,0.08);
        transform: translateY(-1px);
    }
    .tool-btn-icon {
        width: 32px; height: 32px; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 15px; flex-shrink: 0;
    }
    .tool-btn-text { display: flex; flex-direction: column; gap: 1px; }
    .tool-btn-label { font-weight: 600; font-size: 13px; }
    .tool-btn-desc { font-size: 11px; color: var(--text-muted); font-weight: 400; }

    .tool-btn-news .tool-btn-icon { background: #eff6ff; color: #3b82f6; }
    .tool-btn-prices .tool-btn-icon { background: #ecfdf5; color: #10b981; }
    .tool-btn-earnings .tool-btn-icon { background: #fefce8; color: #f59e0b; }
    .tool-btn-ingest .tool-btn-icon { background: #faf5ff; color: #8b5cf6; }

    .sidebar-divider {
        height: 1px; background: var(--border);
        margin: 12px 0;
    }

    /* --- Tool cards --- */
    .tool-card {
        border: 1px solid var(--border);
        border-radius: 14px; padding: 20px;
        margin: 12px 0; background: white;
        box-shadow: var(--shadow-sm);
        animation: slideUp 0.3s ease;
    }
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .tool-card h4 {
        font-size: 14px; font-weight: 700; color: var(--text-primary);
        margin: 0 0 12px; display: flex; align-items: center; gap: 8px;
    }
    .tool-card-badge {
        font-size: 10px; font-weight: 600; padding: 2px 8px;
        border-radius: 100px; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .badge-news { background: #eff6ff; color: #3b82f6; }
    .badge-prices { background: #ecfdf5; color: #10b981; }
    .badge-earnings { background: #fefce8; color: #f59e0b; }
    .badge-ingest { background: #faf5ff; color: #8b5cf6; }
    .badge-error { background: #fef2f2; color: var(--danger); }

    .news-item {
        padding: 12px 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .news-item:last-child { border-bottom: none; }
    .news-headline {
        font-size: 13px; font-weight: 600; color: var(--text-primary);
        margin: 0 0 4px; line-height: 1.4;
    }
    .news-meta {
        display: flex; gap: 8px; align-items: center;
        margin: 0 0 6px;
    }
    .news-label {
        font-size: 10px; font-weight: 600; padding: 2px 8px;
        border-radius: 100px; background: #f1f5f9; color: var(--text-secondary);
    }
    .news-sentiment-positive { background: #ecfdf5; color: #10b981; }
    .news-sentiment-negative { background: #fef2f2; color: #ef4444; }
    .news-sentiment-neutral { background: #f1f5f9; color: #64748b; }
    .news-bullets {
        font-size: 12px; color: var(--text-secondary);
        margin: 0; line-height: 1.5; white-space: pre-wrap;
    }

    .price-stat {
        display: flex; align-items: baseline; gap: 8px;
        margin: 0 0 4px;
    }
    .price-value {
        font-size: 28px; font-weight: 700; color: var(--text-primary);
        letter-spacing: -0.5px;
    }
    .price-label {
        font-size: 12px; color: var(--text-muted);
    }
    .price-detail {
        font-size: 12px; color: var(--text-secondary); margin: 4px 0 0;
    }

    .earnings-event {
        display: flex; align-items: center; gap: 12px;
        padding: 10px 0; border-bottom: 1px solid #f1f5f9;
    }
    .earnings-event:last-child { border-bottom: none; }
    .earnings-date-box {
        width: 48px; height: 48px; border-radius: 10px;
        background: #fefce8; display: flex; flex-direction: column;
        align-items: center; justify-content: center; flex-shrink: 0;
    }
    .earnings-date-month {
        font-size: 10px; font-weight: 700; color: #f59e0b;
        text-transform: uppercase;
    }
    .earnings-date-day {
        font-size: 18px; font-weight: 700; color: #92400e;
        line-height: 1;
    }
    .earnings-info { display: flex; flex-direction: column; gap: 2px; }
    .earnings-eps {
        font-size: 13px; font-weight: 600; color: var(--text-primary);
    }
    .earnings-hour {
        font-size: 11px; color: var(--text-muted);
    }

    .error-card {
        border: 1px solid #fecaca;
        background: #fef2f2;
        border-radius: 14px; padding: 16px 20px;
        margin: 12px 0;
        animation: slideUp 0.3s ease;
    }
    .error-card p {
        color: var(--danger); margin: 0;
        font-size: 13px; display: flex; align-items: center; gap: 8px;
    }

    /* --- Loading spinner (htmx) --- */
    .htmx-indicator {
        display: none;
    }
    .htmx-request .htmx-indicator,
    .htmx-request.htmx-indicator {
        display: inline-flex;
    }
    .loading-dots {
        display: inline-flex; gap: 4px; padding: 8px 0;
    }
    .loading-dots span {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--accent); opacity: 0.3;
        animation: dotPulse 1.4s infinite ease-in-out both;
    }
    .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
    .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
    @keyframes dotPulse {
        0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
        40% { opacity: 1; transform: scale(1); }
    }

    /* --- Action toast (htmx indicator, reused per long-running button) --- */
    .action-toast {
        position: fixed;
        top: 24px; right: 24px;
        background: linear-gradient(135deg, var(--usd-founders), var(--usd-immaculata));
        color: white;
        padding: 14px 20px;
        border-radius: 12px;
        box-shadow: var(--shadow-xl);
        font-size: 13px; font-weight: 500;
        z-index: 1000;
        display: none;
        align-items: center; gap: 14px;
        max-width: 360px;
        line-height: 1.4;
    }
    .action-toast.htmx-request {
        display: flex;
        animation: toastSlideIn 0.25s ease;
    }
    @keyframes toastSlideIn {
        from { opacity: 0; transform: translateX(20px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    .action-toast .loading-dots { padding: 0; }
    .action-toast .loading-dots span { background: white; }
    .action-toast-text {
        display: flex; flex-direction: column; gap: 2px;
    }
    .action-toast-title { font-weight: 600; font-size: 13px; }
    .action-toast-sub {
        font-size: 11px; opacity: 0.85; font-weight: 400;
    }

    /* --- Assessment disclaimer footer --- */
    .assessment-disclaimer {
        margin-top: 14px; padding-top: 12px;
        border-top: 1px dashed var(--border);
    }
    .assessment-disclaimer-text {
        margin: 0;
        font-size: 11px; color: var(--text-muted);
        line-height: 1.55;
    }
    .assessment-disclaimer-text strong { color: var(--text-secondary); }

    /* --- First-run tutorial modal --- */
    .tutorial-modal {
        position: fixed; inset: 0;
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(6px);
        display: flex; align-items: center; justify-content: center;
        z-index: 2000;
        padding: 24px;
        animation: tutorialFadeIn 0.25s ease;
    }
    @keyframes tutorialFadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    .tutorial-modal-card {
        background: white;
        border-radius: 20px;
        padding: 36px 40px;
        max-width: 620px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 30px 60px rgba(0,0,0,0.3);
        animation: tutorialSlideUp 0.35s ease;
    }
    @keyframes tutorialSlideUp {
        from { opacity: 0; transform: translateY(20px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .tutorial-header {
        text-align: center;
        margin-bottom: 24px;
        padding-bottom: 20px;
        border-bottom: 1px solid var(--border);
    }
    .tutorial-header-icon {
        width: 56px; height: 56px; border-radius: 14px;
        background: linear-gradient(135deg, var(--usd-founders), var(--usd-immaculata));
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 14px;
        box-shadow: 0 8px 20px rgba(0,59,112,0.25);
    }
    .tutorial-title {
        font-size: 22px; font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 8px;
        letter-spacing: -0.3px;
    }
    .tutorial-subtitle {
        font-size: 13px; color: var(--text-muted);
        margin: 0 auto; line-height: 1.55;
        max-width: 460px;
    }
    .tutorial-body {
        display: flex; flex-direction: column; gap: 18px;
        margin-bottom: 24px;
    }
    .tutorial-section {
        display: flex; gap: 14px; align-items: flex-start;
    }
    .tutorial-step-num {
        flex-shrink: 0;
        width: 30px; height: 30px; border-radius: 50%;
        background: linear-gradient(135deg, var(--accent), var(--accent-hover));
        color: white;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; font-weight: 700;
        box-shadow: 0 2px 6px rgba(59,130,246,0.35);
    }
    .tutorial-section-text { flex: 1; min-width: 0; }
    .tutorial-section-title {
        font-size: 14px; font-weight: 700;
        color: var(--text-primary);
        margin: 4px 0 4px;
    }
    .tutorial-section-body {
        font-size: 13px; color: var(--text-secondary);
        line-height: 1.6; margin: 0;
    }
    .tutorial-btn {
        width: 100%;
        padding: 14px 24px;
        background: linear-gradient(135deg, var(--accent), var(--accent-hover)) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 14px; font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(59,130,246,0.35);
        transition: transform 0.15s, box-shadow 0.2s;
        font-family: 'Inter', sans-serif;
    }
    .tutorial-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(59,130,246,0.45);
    }
""")


def _chart_icon_svg():
    return NotStr(
        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
        'stroke-width="1.5" stroke="white">'
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 '
        '0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 '
        '0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 '
        '0l-.5 1.5" />'
        '</svg>'
    )


def _arrow_icon_svg():
    return NotStr(
        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
        'stroke-width="2" stroke="currentColor" width="16" height="16">'
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />'
        '</svg>'
    )


def launcher_screen():
    """Polished landing page with glassmorphism card."""
    return (
        Title("Agent Advisor"),
        Div(
            Div(
                Div(_chart_icon_svg(), cls="launcher-icon"),
                H1("Agent Advisor", cls="launcher-title"),
                P("AI-powered financial research copilot. Ask questions about "
                  "Apple's 10-K, track market news, analyze prices, and monitor earnings.",
                  cls="launcher-sub"),
                A("Get Started ", _arrow_icon_svg(),
                  href="/chat?tour=1", cls="launcher-btn"),
                Div(
                    Span("RAG + Ollama", cls="launcher-badge"),
                    Span("Finnhub", cls="launcher-badge"),
                    Span("yFinance", cls="launcher-badge"),
                    Span("LangGraph", cls="launcher-badge"),
                    cls="launcher-badges",
                ),
                cls="launcher-card",
            ),
            cls="launcher-bg",
        ),
    )


def chat_screen(show_tour: bool = False):
    """Two-column layout with an assessment panel plus a tools sidebar.

    ``show_tour`` toggles the first-time tutorial modal, mounted when the
    launcher's Get Started button arrives with ``?tour=1``.
    """
    return (
        Title("Agent Advisor: Stock Assessment"),
        ingest_toast(),
        news_toast(),
        prices_toast(),
        earnings_toast(),
        assessment_toast(),
        tutorial_modal() if show_tour else None,
        Div(
            _chat_main(),
            _tools_sidebar(),
            cls="chat-layout",
        ),
    )


def _loading_toast(toast_id: str, title: str, subtitle: str):
    """Fixed top-right toast used as an htmx indicator for slow buttons.

    The toast lives permanently in the DOM with ``display:none``; htmx
    adds the ``htmx-request`` class to the element referenced by
    ``hx-indicator`` for the duration of the request, which flips it to
    ``display:flex``. Auto-hides on response.
    """
    return Div(
        Div(Span(), Span(), Span(), cls="loading-dots"),
        Div(
            Span(title, cls="action-toast-title"),
            Span(subtitle, cls="action-toast-sub"),
            cls="action-toast-text",
        ),
        id=toast_id,
        cls="action-toast",
    )


def ingest_toast():
    return _loading_toast(
        "ingest-toast",
        "Ingesting PDFs…",
        "This can take a couple of minutes.",
    )


def news_toast():
    return _loading_toast(
        "news-toast",
        "Fetching market news…",
        "Classifying and summarizing articles; this can take a minute.",
    )


def _chat_main():
    return Div(
        Div(
            Div(
                Span(cls="chat-header-dot"),
                "AAPL Stock Assessment",
                cls="chat-header-title",
            ),
            P(
                "One click to synthesize macro news, recent price action, upcoming "
                "earnings, and 10-K context into a grounded near-term view.",
                cls="chat-header-sub",
            ),
            cls="chat-header",
        ),
        Div(
            _assessment_placeholder(),
            id="assessment-output",
            cls="chat-thread",
        ),
        Div(
            assessment_button(),
            cls="chat-input-bar",
        ),
        cls="chat-main",
    )


def _assessment_placeholder():
    return Div(
        Div(_chart_icon_dark_svg(), cls="assessment-placeholder-icon"),
        P("Ready when you are.", cls="assessment-placeholder-title"),
        P(
            "Click Generate below to run the full assessment graph. "
            "This takes a couple of minutes the first time.",
            cls="assessment-placeholder-sub",
        ),
        cls="assessment-placeholder",
    )


def _chart_icon_dark_svg():
    return NotStr(
        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
        'stroke-width="1.6" stroke="currentColor" width="28" height="28">'
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M3 13.5l4.5-4.5 3 3 5-5 5.5 5.5M3 20.25h18" />'
        '</svg>'
    )


def _spark_icon_svg():
    return NotStr(
        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
        'stroke-width="1.8" stroke="white" width="24" height="24">'
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 '
        '4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 '
        '4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 '
        '6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 '
        '2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 '
        '2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423L16.5 15.75l.394 1.183a2.25 '
        '2.25 0 001.423 1.423L19.5 18.75l-1.183.394a2.25 2.25 0 00-1.423 1.423z" />'
        '</svg>'
    )


def assessment_button():
    """Big branded CTA — replaces the old free-form chat input."""
    return Div(
        Button(
            Div(_spark_icon_svg(), cls="assessment-btn-icon"),
            Div(
                Span("Generate AAPL Assessment", cls="assessment-btn-label"),
                Span(
                    "News + prices + earnings + 10-K synthesis",
                    cls="assessment-btn-sub",
                ),
                cls="assessment-btn-text",
            ),
            Span(_arrow_icon_svg(), cls="assessment-btn-arrow"),
            hx_post="/assessment",
            hx_target="#assessment-output",
            hx_swap="innerHTML",
            hx_indicator="#assessment-toast",
            hx_disabled_elt="this",
            cls="assessment-btn",
            type="button",
        ),
        cls="assessment-btn-wrap",
    )


def _tool_button(label, desc, icon_text, css_class, **kwargs):
    return Button(
        Div(Span(icon_text), cls="tool-btn-icon"),
        Div(
            Span(label, cls="tool-btn-label"),
            Span(desc, cls="tool-btn-desc"),
            cls="tool-btn-text",
        ),
        cls=f"tool-btn {css_class}",
        **kwargs,
    )


def _tools_sidebar():
    return Div(
        Div(H4("Tools"), cls="sidebar-header"),
        Div(
            _tool_button(
                "Market News", "Finnhub categorized feed",
                "N", "tool-btn-news",
                hx_get="/tools/news",
                hx_target="#tool-output",
                hx_swap="innerHTML",
                hx_indicator="#news-toast",
            ),
            _tool_button(
                "AAPL Prices", "120-day OHLCV history",
                "$", "tool-btn-prices",
                hx_get="/tools/prices?symbol=AAPL",
                hx_target="#tool-output",
                hx_swap="innerHTML",
                hx_indicator="#prices-toast",
            ),
            _tool_button(
                "AAPL Earnings", "Upcoming calendar",
                "E", "tool-btn-earnings",
                hx_get="/tools/earnings?ticker=AAPL",
                hx_target="#tool-output",
                hx_swap="innerHTML",
                hx_indicator="#earnings-toast",
            ),
            Div(cls="sidebar-divider"),
            _tool_button(
                "Ingest PDFs", "Load docs into Chroma",
                "I", "tool-btn-ingest",
                hx_post="/tools/ingest",
                hx_target="#tool-output",
                hx_swap="innerHTML",
                hx_indicator="#ingest-toast",
            ),
            Div(id="tool-output"),
            cls="sidebar-body",
        ),
        cls="tools-sidebar",
    )


def assessment_toast():
    return _loading_toast(
        "assessment-toast",
        "Analyzing AAPL…",
        "Fetching news, prices, earnings, retrieving 10-K context, and "
        "synthesizing. This takes a couple of minutes.",
    )


def prices_toast():
    return _loading_toast(
        "prices-toast",
        "Fetching AAPL prices…",
        "Pulling the last 90 trading sessions from Yahoo Finance.",
    )


def earnings_toast():
    return _loading_toast(
        "earnings-toast",
        "Fetching AAPL earnings…",
        "Looking up upcoming earnings events from Finnhub.",
    )


def _tutorial_section(step: str, title: str, body: str):
    return Div(
        Span(step, cls="tutorial-step-num"),
        Div(
            H3(title, cls="tutorial-section-title"),
            P(body, cls="tutorial-section-body"),
            cls="tutorial-section-text",
        ),
        cls="tutorial-section",
    )


def tutorial_modal():
    """First-run walkthrough shown when the launcher sends ``?tour=1``.

    Deliberately non-technical — covers the main flow, the sidebar tools,
    and the 'what's running under the hood' context so a teammate or
    hiring manager can pick it up cold. Dismiss is a one-line inline
    ``onclick`` that removes the modal node (no JS framework needed).
    """
    return Div(
        Div(
            Div(
                Div(_spark_icon_svg(), cls="tutorial-header-icon"),
                H2("Welcome to Agent Advisor", cls="tutorial-title"),
                P(
                    "Your local AI copilot for Apple stock research. "
                    "Everything runs on your machine, with no cloud and no paid APIs.",
                    cls="tutorial-subtitle",
                ),
                cls="tutorial-header",
            ),
            Div(
                _tutorial_section(
                    "1",
                    "Generate an assessment",
                    "Click the big blue button to run the full analysis pipeline. "
                    "In about two minutes you'll get a one-sentence thesis, a "
                    "bullish / neutral / bearish outlook badge, bull and bear case "
                    "bullets, upcoming catalysts, and key risks, all grounded "
                    "in live market signals and passages from Apple's 2024 10-K.",
                ),
                _tutorial_section(
                    "2",
                    "Jump to raw data with the sidebar",
                    "The right-hand sidebar is for quick drill-downs without "
                    "running the full pipeline. Market News shows macro-level "
                    "headlines (broader than Apple, so it complements the "
                    "assessment rather than duplicating it). AAPL Prices and "
                    "AAPL Earnings pull live data on demand. Ingest PDFs loads "
                    "reference documents into the knowledge base.",
                ),
                _tutorial_section(
                    "3",
                    "What's running under the hood",
                    "Language models are served locally by Ollama. Apple's 2024 "
                    "10-K filing is stored as embeddings in Chroma. Every bullet "
                    "in the assessment is tied to a specific signal, and the model "
                    "is explicitly instructed never to fabricate. This is a "
                    "research and education tool, not investment advice.",
                ),
                cls="tutorial-body",
            ),
            Button(
                "Got it, let's go",
                onclick="this.closest('.tutorial-modal').remove()",
                cls="tutorial-btn",
                type="button",
            ),
            cls="tutorial-modal-card",
        ),
        cls="tutorial-modal",
        id="tutorial-modal",
    )


def error_card(message: str):
    return Div(
        P(NotStr("&#x26A0;"), " ", message),
        cls="error-card",
    )


def _sentiment_class(sentiment: str) -> str:
    s = (sentiment or "").lower()
    if "positive" in s or "bullish" in s:
        return "news-sentiment-positive"
    if "negative" in s or "bearish" in s:
        return "news-sentiment-negative"
    return "news-sentiment-neutral"


def news_card(payload: dict):
    if "error" in payload:
        return error_card(f"News: {payload['error']}")
    analyses = payload.get("analyses", [])
    if not analyses:
        return Div(P("No news articles returned.", style="margin:0; color:var(--text-muted);"), cls="tool-card")
    items = [
        Div(
            P(a.get("headline", "(no headline)"), cls="news-headline"),
            Div(
                Span(a.get("label", "?"), cls="news-label"),
                Span(a.get("sentiment", "?"),
                     cls=f"news-label {_sentiment_class(a.get('sentiment', ''))}"),
                cls="news-meta",
            ),
            P(a.get("bullets", ""), cls="news-bullets") if a.get("bullets") else None,
            cls="news-item",
        )
        for a in analyses
    ]
    cat = payload.get("category", "general")
    return Div(
        H4(
            f"Market News",
            Span(cat.title(), cls="tool-card-badge badge-news"),
        ),
        *items,
        cls="tool-card",
    )


def prices_card(payload: dict):
    if "error" in payload:
        return error_card(f"Prices: {payload['error']}")
    rows = payload.get("data", [])
    if not rows:
        return Div(P("No price data returned.", style="margin:0; color:var(--text-muted);"), cls="tool-card")
    last = rows[-1]
    close = last.get("Close")
    close_str = f"${close:,.2f}" if isinstance(close, (int, float)) else str(close)
    return Div(
        H4(
            f"{payload.get('symbol', '?')} Price History",
            Span("OHLCV", cls="tool-card-badge badge-prices"),
        ),
        Div(
            Span(close_str, cls="price-value"),
            Span("last close", cls="price-label"),
            cls="price-stat",
        ),
        P(
            f"{payload.get('rows', 0)} data points  |  "
            f"TA indicators: {'available' if payload.get('indicators_available') else 'n/a'}",
            cls="price-detail",
        ),
        cls="tool-card",
    )


def _parse_earnings_date(date_str: str):
    parts = date_str.split("-") if date_str else []
    if len(parts) == 3:
        months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        try:
            return months[int(parts[1])], parts[2]
        except (ValueError, IndexError):
            pass
    return "??", "??"


def earnings_card(payload: dict):
    if "error" in payload:
        return error_card(f"Earnings: {payload['error']}")
    cal = payload.get("calendar") or {}
    events = cal.get("earningsCalendar") or []
    ticker = payload.get("ticker", "?")
    if not events:
        return Div(
            H4(
                f"{ticker} Earnings",
                Span("Calendar", cls="tool-card-badge badge-earnings"),
            ),
            P("No upcoming earnings within the lookahead window.",
              style="margin:0; color:var(--text-muted); font-size:13px;"),
            cls="tool-card",
        )
    items = []
    for e in events:
        month, day = _parse_earnings_date(e.get("date", ""))
        hour = e.get("hour", "?")
        hour_label = {"bmo": "Before market open", "amc": "After market close"}.get(hour, hour)
        items.append(
            Div(
                Div(
                    Span(month, cls="earnings-date-month"),
                    Span(day, cls="earnings-date-day"),
                    cls="earnings-date-box",
                ),
                Div(
                    Span(f"EPS est: {e.get('epsEstimate', 'N/A')}", cls="earnings-eps"),
                    Span(hour_label, cls="earnings-hour"),
                    cls="earnings-info",
                ),
                cls="earnings-event",
            )
        )
    return Div(
        H4(
            f"{ticker} Earnings",
            Span("Calendar", cls="tool-card-badge badge-earnings"),
        ),
        *items,
        cls="tool-card",
    )


def ingest_card(payload: dict):
    if "error" in payload:
        return error_card(f"Ingest: {payload['error']}")

    new = payload.get("new", 0)
    skipped = payload.get("skipped", 0)
    total = payload.get("total", 0)
    files = payload.get("files", 0)
    note = payload.get("note", "")

    if total == 0:
        headline = "No chunks to ingest."
    elif new == 0:
        headline = (
            f"Already up to date. All {total} chunks from "
            f"{files} file(s) were already indexed."
        )
    elif skipped == 0:
        headline = f"Indexed {new} new chunks from {files} file(s)."
    else:
        headline = (
            f"Indexed {new} new chunks from {files} file(s); "
            f"skipped {skipped} already in the store."
        )

    return Div(
        H4(
            "PDF Ingest",
            Span("Complete", cls="tool-card-badge badge-ingest"),
        ),
        P(headline, style="margin:0; font-size:13px; color:var(--text-primary);"),
        P(note, style="margin:6px 0 0 0; font-size:12px; color:var(--text-muted);")
        if note
        else None,
        cls="tool-card",
    )


def _assessment_list(items: list[str]):
    if not items:
        return P("(insufficient data)", cls="assessment-empty")
    return Ul(*[Li(item) for item in items], cls="assessment-list")


def assessment_card(payload: dict):
    """Render the StockAssessment payload as a pretty grounded card."""
    if "error" in payload:
        return error_card(f"Assessment: {payload['error']}")

    ticker = payload.get("ticker", "?")
    rag_query = payload.get("rag_query", "")
    assessment = payload.get("assessment") or {}

    thesis = assessment.get("thesis") or "(no thesis generated)"
    outlook = (assessment.get("outlook") or "neutral").lower()
    bull = assessment.get("bull_case") or []
    bear = assessment.get("bear_case") or []
    catalysts = assessment.get("catalysts") or []
    risks = assessment.get("risks") or []

    outlook_class = {
        "bullish": "outlook-bullish",
        "neutral": "outlook-neutral",
        "bearish": "outlook-bearish",
    }.get(outlook, "outlook-neutral")

    return Div(
        Div(
            H3(f"{ticker} Near-Term Assessment", cls="assessment-title"),
            Span(outlook.title(), cls=f"outlook-badge {outlook_class}"),
            cls="assessment-header",
        ),
        P(thesis, cls="assessment-thesis"),
        Div(
            Div(
                H4("Bull Case", cls="assessment-section-title"),
                _assessment_list(bull),
                cls="assessment-column assessment-column-bull",
            ),
            Div(
                H4("Bear Case", cls="assessment-section-title"),
                _assessment_list(bear),
                cls="assessment-column assessment-column-bear",
            ),
            cls="assessment-grid",
        ),
        Div(
            H4("Catalysts", cls="assessment-section-title"),
            _assessment_list(catalysts),
            cls="assessment-block assessment-block-catalysts",
        ),
        Div(
            H4("Risks", cls="assessment-section-title"),
            _assessment_list(risks),
            cls="assessment-block assessment-block-risks",
        ),
        Div(
            Span("RAG query:", cls="assessment-query-label"),
            Span(rag_query, cls="assessment-query-text"),
            cls="assessment-query",
        ) if rag_query else None,
        Div(
            P(
                NotStr("&#9432;"), " ",
                "10-K context is grounded in Apple's ",
                Strong("2024"),
                " annual filing and does not reflect anything dated after "
                "that filing. Live signals come from Finnhub and Yahoo "
                "Finance on a best-effort basis — article summaries may be "
                "truncated upstream, prices are delayed rather than real-time, "
                "and consensus estimates revise. The assessment is generated "
                "by a small local LLM (llama3.2 via Ollama) which can "
                "hallucinate, confuse entities, and mis-cite sources; verify "
                "every bullet against primary sources before acting on it. "
                "Research and education only: ",
                Strong("not investment, tax, legal, or financial advice"),
                ".",
                cls="assessment-disclaimer-text",
            ),
            cls="assessment-disclaimer",
        ),
        cls="assessment-card",
    )

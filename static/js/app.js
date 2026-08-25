/**
 * 星尘 · 个人智能助手 — 前端逻辑
 * SSE 流式对话 · Markdown 渲染 · 会话记忆 · 健康检查
 */
(function () {
  'use strict';

  const API_BASE = window.location.origin;
  let threadId = null;
  let streaming = false;
  let abortController = null;

  // DOM
  const chatEl = document.getElementById('chat');
  const inputEl = document.getElementById('input');
  const sendBtn = document.getElementById('sendBtn');
  const composerBox = document.getElementById('composerBox');
  const clearBtn = document.getElementById('clearBtn');
  const newChatBtn = document.getElementById('newChatBtn');
  const menuBtn = document.getElementById('menuBtn');
  const sidebar = document.getElementById('sidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const statusDot = document.getElementById('statusDot');
  const connText = document.getElementById('connText');
  const msgCountEl = document.getElementById('msgCount');

  const ICON_COPY =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
  const ICON_CHECK =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
  const ICON_SPARK =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"/></svg>';

  /* ================= Markdown 渲染 ================= */

  function escapeHtml(s) {
    return s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function inlineFormat(s) {
    return s
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>')
      .replace(/~~(.+?)~~/g, '<del>$1</del>')
      .replace(/`([^`\n]+)`/g, '<code>$1</code>')
      .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
  }

  function renderTable(rows) {
    const parse = (r) =>
      r.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map((c) => c.trim());
    const head = parse(rows[0]);
    let body = rows.slice(1);
    if (body.length && /^[\s|:—-]+$/.test(body[0])) body = body.slice(1);
    let html =
      '<div class="table-wrap"><table><thead><tr>' +
      head.map((h) => `<th>${inlineFormat(h)}</th>`).join('') +
      '</tr></thead><tbody>';
    for (const row of body) {
      html += '<tr>' + parse(row).map((c) => `<td>${inlineFormat(c)}</td>`).join('') + '</tr>';
    }
    return html + '</tbody></table></div>';
  }

  function renderMarkdown(text) {
    if (!text) return '';

    const codeBlocks = [];
    let src = escapeHtml(text);
    src = src.replace(/```(\w+)?\s*\n?([\s\S]*?)```/g, (m, lang, code) => {
      codeBlocks.push(
        '<pre class="code-block"><div class="code-head"><span class="dots"><i></i><i></i><i></i></span>' +
          (lang || 'code') +
          '</div><code>' +
          code.replace(/^\n+|\n+$/g, '') +
          '</code></pre>'
      );
      return '\u0000CB' + (codeBlocks.length - 1) + '\u0000';
    });

    const lines = src.split('\n');
    const out = [];
    let list = null;

    const closeList = () => {
      if (list) {
        out.push('</' + list + '>');
        list = null;
      }
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // 代码块占位
      const cb = line.match(/^\u0000CB(\d+)\u0000$/);
      if (cb) {
        closeList();
        out.push(codeBlocks[+cb[1]]);
        continue;
      }

      // 标题
      const h = line.match(/^(#{1,4})\s+(.*)$/);
      if (h) {
        closeList();
        const level = Math.min(h[1].length + 1, 4);
        out.push(`<h${level}>${inlineFormat(h[2])}</h${level}>`);
        continue;
      }

      // 表格
      if (/^\s*\|.+\|\s*$/.test(line)) {
        closeList();
        const rows = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
          rows.push(lines[i]);
          i++;
        }
        i--;
        out.push(renderTable(rows));
        continue;
      }

      // 引用
      const bq = line.match(/^&gt;\s?(.*)$/);
      if (bq) {
        closeList();
        out.push(`<blockquote>${inlineFormat(bq[1])}</blockquote>`);
        continue;
      }

      // 分隔线
      if (/^-{3,}\s*$/.test(line)) {
        closeList();
        out.push('<hr>');
        continue;
      }

      // 无序列表
      const ul = line.match(/^[-*]\s+(.*)$/);
      if (ul) {
        if (list !== 'ul') {
          closeList();
          list = 'ul';
          out.push('<ul>');
        }
        out.push(`<li>${inlineFormat(ul[1])}</li>`);
        continue;
      }

      // 有序列表
      const ol = line.match(/^\d+[.)]\s+(.*)$/);
      if (ol) {
        if (list !== 'ol') {
          closeList();
          list = 'ol';
          out.push('<ol>');
        }
        out.push(`<li>${inlineFormat(ol[1])}</li>`);
        continue;
      }

      // 空行
      closeList();
      if (!line.trim()) continue;
      out.push(`<p>${inlineFormat(line.trim())}</p>`);
    }
    closeList();

    return out.join('\n');
  }

  /* ================= 消息渲染 ================= */

  function nowTime() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  function renderWelcome() {
    const el = document.createElement('div');
    el.className = 'welcome';
    el.innerHTML = `
      <div class="welcome-avatar">${ICON_SPARK}</div>
      <h2>你好，我是 <span class="grad">星尘</span></h2>
      <p class="welcome-sub">你的个人智能助手，帮你管理日程、待办与邮件，智能规划每一天。</p>
      <div class="welcome-cards">
        <button class="w-card" data-quick="帮我看看明天的日程">
          <span class="w-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></span>
          <b>明天日程</b><span class="w-desc">查看完整日程安排</span>
        </button>
        <button class="w-card" data-quick="根据我的 Todo 和邮件，帮我安排一下明天的工作">
          <span class="w-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></span>
          <b>智能安排明天</b><span class="w-desc">生成最优工作计划</span>
        </button>
        <button class="w-card" data-quick="检查明天有没有时间冲突，给我提出调整建议">
          <span class="w-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span>
          <b>冲突检测</b><span class="w-desc">发现时间冲突与建议</span>
        </button>
        <button class="w-card" data-quick="查看我的未读邮件">
          <span class="w-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></span>
          <b>未读邮件</b><span class="w-desc">快速处理重要邮件</span>
        </button>
      </div>`;
    chatEl.appendChild(el);
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  function addMessage(role, content, opts = {}) {
    const wrap = document.createElement('div');
    wrap.className = `msg ${role}`;

    const meta =
      role === 'ai'
        ? `<div class="msg-meta"><span class="msg-time">${opts.time || nowTime()}</span>` +
          `<button class="copy-btn" title="复制回答">${ICON_COPY}<span>复制</span></button></div>`
        : `<div class="msg-meta"><span class="msg-time">${opts.time || nowTime()}</span></div>`;

    if (role === 'ai') {
      wrap.innerHTML = `
        <div class="avatar">${ICON_SPARK}</div>
        <div class="msg-body">
          <div class="bubble">
            ${opts.tool ? `<span class="tool-badge"><span class="spinner"></span>正在调用 ${opts.tool}</span>` : ''}
            <div class="content">${opts.streaming ? '' : renderMarkdown(content)}</div>
            ${opts.streaming ? '<div class="typing"><span></span><span></span><span></span></div>' : ''}
          </div>
          ${meta}
        </div>`;
    } else {
      wrap.innerHTML = `
        <div class="msg-body">
          <div class="bubble">${escapeHtml(content).replace(/\n/g, '<br>')}</div>
          ${meta}
        </div>`;
    }

    chatEl.appendChild(wrap);
    chatEl.scrollTop = chatEl.scrollHeight;
    return wrap;
  }

  function addToolBadge(aiDiv, name) {
    const bubble = aiDiv.querySelector('.bubble');
    const badge = aiDiv.querySelector('.tool-badge');
    if (badge) badge.remove();
    const el = document.createElement('span');
    el.className = 'tool-badge';
    el.innerHTML = `<span class="spinner"></span>正在调用 ${escapeHtml(name)}`;
    bubble.insertBefore(el, bubble.firstChild);
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  function finishToolBadge(aiDiv) {
    const badge = aiDiv.querySelector('.tool-badge');
    if (badge) {
      badge.classList.add('done');
      badge.innerHTML = `${ICON_CHECK}<span>工具执行完成</span>`;
      setTimeout(() => badge.remove(), 1600);
    }
  }

  function updateStreamingContent(aiDiv, text, streaming) {
    const contentEl = aiDiv.querySelector('.content');
    const typingEl = aiDiv.querySelector('.typing');
    if (!contentEl) return;
    const cursor = streaming ? '<span class="stream-cursor"></span>' : '';
    contentEl.innerHTML = renderMarkdown(text) + cursor;
    if (typingEl) typingEl.remove();
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  function updateMsgCount() {
    const count = chatEl.querySelectorAll('.msg').length;
    msgCountEl.textContent = count ? `${count} 条消息` : '开始一段对话吧';
  }

  /* ================= 发送 / 流式 ================= */

  function setStreamingUI(on) {
    streaming = on;
    sendBtn.classList.toggle('streaming', on);
    sendBtn.title = on ? '停止生成' : '发送消息 (Enter)';
    if (on) {
      abortController = new AbortController();
    } else {
      abortController = null;
    }
  }

  async function sendMessage(text) {
    text = (text || '').trim();
    if (!text || streaming) return;

    setStreamingUI(true);
    inputEl.value = '';
    autoGrow();

    addMessage('user', text);
    const aiDiv = addMessage('ai', '', { streaming: true });
    updateMsgCount();

    let fullText = '';
    let lastTool = null;

    try {
      const res = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, thread_id: threadId }),
        signal: abortController.signal,
      });

      if (!res.ok) throw new Error(`服务返回 HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          let data;
          try {
            data = JSON.parse(line.slice(6));
          } catch {
            continue;
          }

          if (data.type === 'token') {
            if (lastTool) {
              finishToolBadge(aiDiv);
              lastTool = null;
            }
            fullText += data.content;
            updateStreamingContent(aiDiv, fullText, true);
          } else if (data.type === 'tool_start') {
            lastTool = data.name;
            addToolBadge(aiDiv, data.name);
          } else if (data.type === 'tool_end') {
            finishToolBadge(aiDiv);
            lastTool = null;
          } else if (data.type === 'done') {
            threadId = data.thread_id;
          } else if (data.type === 'error') {
            fullText = `请求出错：${data.content}`;
          }
        }
      }

      if (fullText) {
        updateStreamingContent(aiDiv, fullText, false);
      } else if (!abortController || !abortController.signal.aborted) {
        updateStreamingContent(aiDiv, '（没有返回内容）', false);
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        if (fullText) updateStreamingContent(aiDiv, fullText, false);
        else aiDiv.remove();
      } else {
        const msg =
          '连接失败：' +
          err.message +
          '\n\n请确认后端服务已启动（python main.py，端口 8010）。';
        updateStreamingContent(aiDiv, fullText || msg, false);
      }
    } finally {
      setStreamingUI(false);
      updateMsgCount();
      inputEl.focus();
    }
  }

  /* ================= 输入框 ================= */

  function autoGrow() {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 180) + 'px';
  }

  /* ================= 会话管理 ================= */

  function resetChat(showWelcome) {
    if (streaming && abortController) abortController.abort();
    chatEl.innerHTML = '';
    threadId = null;
    if (showWelcome) renderWelcome();
    updateMsgCount();
  }

  /* ================= 健康检查 ================= */

  async function checkHealth() {
    statusDot.className = 'status-dot pending';
    connText.textContent = '正在连接服务…';
    try {
      const res = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(5000) });
      if (!res.ok) throw new Error('bad status');
      const data = await res.json();
      if (data.status === 'ok') {
        statusDot.className = 'status-dot';
        connText.textContent = `服务在线 · :8010`;
      } else {
        throw new Error('unexpected');
      }
    } catch {
      statusDot.className = 'status-dot offline';
      connText.textContent = '服务未连接';
    }
  }

  /* ================= 复制 ================= */

  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
      const label = btn.querySelector('span');
      const prev = label ? label.textContent : '';
      btn.innerHTML = ICON_CHECK + '<span>已复制</span>';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.innerHTML = ICON_COPY + '<span>复制</span>';
        btn.classList.remove('copied');
        if (label && prev) label.textContent = prev;
      }, 1800);
    } catch {
      /* clipboard 不可用时静默 */
    }
  }

  /* ================= 事件绑定 ================= */

  sendBtn.addEventListener('click', () => {
    if (streaming && abortController) {
      abortController.abort();
      return;
    }
    sendMessage(inputEl.value);
  });

  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputEl.value);
    }
  });

  inputEl.addEventListener('input', autoGrow);

  // 事件委托：快捷按钮 / 欢迎卡片 / 复制
  document.addEventListener('click', (e) => {
    const quick = e.target.closest('[data-quick]');
    if (quick) {
      sendMessage(quick.getAttribute('data-quick'));
      return;
    }
    const copyBtn = e.target.closest('.copy-btn');
    if (copyBtn) {
      const msgBody = copyBtn.closest('.msg-body');
      const bubble = msgBody.querySelector('.bubble');
      const text = bubble.innerText || bubble.textContent;
      copyText(text, copyBtn);
      return;
    }
  });

  newChatBtn.addEventListener('click', () => resetChat(true));
  clearBtn.addEventListener('click', () => {
    resetChat(false);
    renderWelcome();
  });

  menuBtn.addEventListener('click', () => {
    sidebar.classList.add('open');
    sidebarBackdrop.classList.add('show');
  });
  sidebarBackdrop.addEventListener('click', () => {
    sidebar.classList.remove('open');
    sidebarBackdrop.classList.remove('show');
  });

  /* ================= 初始化 ================= */

  renderWelcome();
  updateMsgCount();
  checkHealth();
  setInterval(checkHealth, 20000);
  inputEl.focus();
})();

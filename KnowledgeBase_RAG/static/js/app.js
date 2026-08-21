(() => {
  const $ = (sel) => document.querySelector(sel);
  const messagesEl = $("#messages");
  const inputEl = $("#input");
  const sendBtn = $("#sendBtn");
  const useRagEl = $("#useRag");
  let sessionId = localStorage.getItem("kb_session") || crypto.randomUUID();
  localStorage.setItem("kb_session", sessionId);

  function appendBubble(role, text, sources = []) {
    const div = document.createElement("div");
    div.className = `msg-bubble ${role}`;
    div.textContent = text;

    if (sources && sources.length) {
      const srcWrap = document.createElement("div");
      srcWrap.className = "sources";
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = `查看来源（${sources.length}）`;
      details.appendChild(summary);
      sources.forEach((s, i) => {
        const item = document.createElement("div");
        item.className = "src-item";
        item.textContent = `[${i + 1}] ${s}`;
        details.appendChild(item);
      });
      srcWrap.appendChild(details);
      div.appendChild(srcWrap);
    }

    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  async function refreshStats() {
    try {
      const [statsRes, docsRes] = await Promise.all([
        fetch("/api/stats"),
        fetch("/api/documents"),
      ]);
      const stats = await statsRes.json();
      const docs = await docsRes.json();
      $("#stats").innerHTML = `
        文档：<strong>${stats.total_documents}</strong><br/>
        知识片段：<strong>${stats.total_chunks}</strong><br/>
        集合：${stats.collection_name}
      `;
      const list = $("#docList");
      list.innerHTML = "";
      (docs.documents || []).forEach((d) => {
        const li = document.createElement("li");
        li.innerHTML = `<span>${d.filename}</span> · ${d.chunks} 块`;
        list.appendChild(li);
      });
      if (!(docs.documents || []).length) {
        list.innerHTML = "<li>暂无文档</li>";
      }
    } catch (e) {
      $("#stats").textContent = "无法连接后端";
    }
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = "";
    appendBubble("user", text);
    const loading = appendBubble("assistant", "思考中");
    loading.classList.add("loading");
    sendBtn.disabled = true;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          use_rag: useRagEl.checked,
        }),
      });
      const data = await res.json();
      loading.classList.remove("loading");
      if (!res.ok) {
        loading.textContent = data.detail || "请求失败";
      } else {
        loading.textContent = data.answer || "(空回复)";
        if (data.sources && data.sources.length) {
          const srcWrap = document.createElement("div");
          srcWrap.className = "sources";
          const details = document.createElement("details");
          const summary = document.createElement("summary");
          summary.textContent = `查看来源（${data.sources.length}）`;
          details.appendChild(summary);
          data.sources.forEach((s, i) => {
            const item = document.createElement("div");
            item.className = "src-item";
            item.textContent = `[${i + 1}] ${s}`;
            details.appendChild(item);
          });
          srcWrap.appendChild(details);
          loading.appendChild(srcWrap);
        }
        if (data.session_id) sessionId = data.session_id;
      }
    } catch (e) {
      loading.classList.remove("loading");
      loading.textContent = "网络错误：" + e.message;
    } finally {
      sendBtn.disabled = false;
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }
  }

  sendBtn.addEventListener("click", sendMessage);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  $("#uploadBtn").addEventListener("click", async () => {
    const file = $("#fileInput").files[0];
    const msg = $("#uploadMsg");
    if (!file) {
      msg.textContent = "请选择文件";
      msg.className = "msg err";
      return;
    }
    const fd = new FormData();
    fd.append("file", file);
    msg.textContent = "上传中…";
    msg.className = "msg";
    try {
      const res = await fetch("/api/upload", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "失败");
      msg.textContent = data.message;
      msg.className = "msg ok";
      refreshStats();
    } catch (e) {
      msg.textContent = e.message;
      msg.className = "msg err";
    }
  });

  $("#pasteBtn").addEventListener("click", async () => {
    const content = $("#pasteText").value.trim();
    const filename = $("#pasteName").value.trim() || "note.md";
    if (!content) return alert("内容为空");
    const fd = new FormData();
    fd.append("content", content);
    fd.append("filename", filename);
    try {
      const res = await fetch("/api/upload_text", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "失败");
      alert(data.message);
      $("#pasteText").value = "";
      refreshStats();
    } catch (e) {
      alert(e.message);
    }
  });

  $("#clearBtn").addEventListener("click", async () => {
    if (!confirm("确定清空全部知识库？")) return;
    await fetch("/api/knowledge", { method: "DELETE" });
    refreshStats();
  });

  refreshStats();
})();

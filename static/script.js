async function saveDiary() {
    const titleEl = document.getElementById("title");
    const contentEl = document.getElementById("content");
    if (!titleEl || !contentEl) return;

    const title = titleEl.value;
    const content = contentEl.value;

    await fetch('/save_diary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content })
    });

    loadDiaries();
}

async function loadDiaries() {
    const diaryList = document.getElementById("diaryList");
    if (!diaryList) return;

    try {
        const res = await fetch('/get_diaries');
        if (!res.ok) return;
        const diaries = await res.json();

        diaryList.innerHTML = "";
        diaries.forEach(d => {
            diaryList.innerHTML += `<h3>${d.title}</h3><p>${d.content}</p><hr>`;
        });
    } catch (err) {
        console.error("Error loading diaries:", err);
    }
}

if (document.getElementById("diaryList")) {
    window.onload = loadDiaries;
}


async function saveDiary() {
    const title = document.getElementById("title").value;
    const content = document.getElementById("content").value;

    await fetch('/save_diary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content })
    });

    loadDiaries();
}

async function loadDiaries() {
    const res = await fetch('/get_diaries');
    const diaries = await res.json();

    const diaryList = document.getElementById("diaryList");
    diaryList.innerHTML = "";

    diaries.forEach(d => {
        diaryList.innerHTML += `<h3>${d.title}</h3><p>${d.content}</p><hr>`;
    });
}

window.onload = loadDiaries;

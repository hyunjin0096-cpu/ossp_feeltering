const inputPage = document.getElementById("inputPage");
const loadingPage = document.getElementById("loadingPage");
const resultPage = document.getElementById("resultPage");

const recordButton = document.getElementById("recordButton");
const audioFile = document.getElementById("audioFile");
const complaintText = document.getElementById("complaintText");

const startButton = document.getElementById("startButton");
const restartButton = document.getElementById("restartButton");

const finalText = document.getElementById("finalText");
const departmentResult = document.getElementById("departmentResult");

let isRecording = false;

// 원형 버튼: 현재는 녹음 시작/종료 UI만 구현
recordButton.addEventListener("click", () => {
    isRecording = !isRecording;

    if (isRecording) {
        recordButton.classList.add("recording");
        recordButton.textContent = "⏹️";
        alert("녹음을 시작합니다 (연동필요🤞)");
    } else {
        recordButton.classList.remove("recording");
        recordButton.textContent = "🎙️";
        alert("녹음 종료하고 저장합니다 🐿️");
    }
});

// 변환하기 버튼
startButton.addEventListener("click", async () => {
    const text = complaintText.value.trim();
    const file = audioFile.files[0];

    if (!text && !file) {
        alert("음성 파일을 업로드하거나 민원 내용을 직접 입력해 주세요.");
        return;
    }

    inputPage.classList.add("hidden");
    loadingPage.classList.remove("hidden");

    const formData = new FormData();
    formData.append("text", text);

    if (file) {
        formData.append("audio", file);
    }

    try {
        const response = await fetch("/process", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        setTimeout(() => {
            loadingPage.classList.add("hidden");
            resultPage.classList.remove("hidden");

            finalText.textContent = result.final_text;
            departmentResult.textContent = result.department;
        }, 1200);

    } catch (error) {
        alert("처리 중 오류가 발생했습니다.");
        console.error(error);

        loadingPage.classList.add("hidden");
        inputPage.classList.remove("hidden");
    }
});

// 처음으로 버튼
restartButton.addEventListener("click", () => {
    complaintText.value = "";
    audioFile.value = "";

    resultPage.classList.add("hidden");
    inputPage.classList.remove("hidden");
});
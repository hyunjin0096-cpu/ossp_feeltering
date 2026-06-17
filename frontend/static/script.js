const imageUploadPage = document.getElementById("imageUploadPage");
const categoryConfirmPage = document.getElementById("categoryConfirmPage");
const inputPage = document.getElementById("inputPage");
const loadingPage = document.getElementById("loadingPage");
const resultPage = document.getElementById("resultPage");

const complaintImage = document.getElementById("complaintImage");
const imagePreviewWrap = document.getElementById("imagePreviewWrap");
const imagePreview = document.getElementById("imagePreview");
const imageAnalyzeButton = document.getElementById("imageAnalyzeButton");
const predictedCategory = document.getElementById("predictedCategory");
const confirmCategoryButton = document.getElementById("confirmCategoryButton");
const reuploadImageButton = document.getElementById("reuploadImageButton");

const recordButton = document.getElementById("recordButton");
const audioFile = document.getElementById("audioFile");
const complaintText = document.getElementById("complaintText");

const startButton = document.getElementById("startButton");
const restartButton = document.getElementById("restartButton");

const finalText = document.getElementById("finalText");
const departmentResult = document.getElementById("departmentResult");

let isRecording = false;
let selectedImageCategory = "";


function showPage(pageElement) {
    imageUploadPage.classList.add("hidden");
    categoryConfirmPage.classList.add("hidden");
    inputPage.classList.add("hidden");
    loadingPage.classList.add("hidden");
    resultPage.classList.add("hidden");

    pageElement.classList.remove("hidden");
}


// 이미지 미리보기
complaintImage.addEventListener("change", () => {
    const file = complaintImage.files[0];

    if (!file) {
        imagePreviewWrap.classList.add("hidden");
        imagePreview.removeAttribute("src");
        return;
    }

    const imageUrl = URL.createObjectURL(file);
    imagePreview.src = imageUrl;
    imagePreviewWrap.classList.remove("hidden");
});


// 이미지 분석하기 버튼
imageAnalyzeButton.addEventListener("click", async () => {
    const imageFile = complaintImage.files[0];

    if (!imageFile) {
        alert("민원 현장 이미지를 먼저 업로드해 주세요.");
        return;
    }

    const formData = new FormData();
    formData.append("image", imageFile);

    try {
        const response = await fetch("/classify-image", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        selectedImageCategory = result.category;
        predictedCategory.textContent = selectedImageCategory;

        showPage(categoryConfirmPage);

    } catch (error) {
        alert("이미지 분석 중 오류가 발생했습니다.");
        console.error(error);
    }
});


// 이미지 분류 결과 확인
confirmCategoryButton.addEventListener("click", () => {
    showPage(inputPage);
});


// 이미지 재업로드
reuploadImageButton.addEventListener("click", () => {
    selectedImageCategory = "";
    complaintImage.value = "";
    imagePreviewWrap.classList.add("hidden");
    imagePreview.removeAttribute("src");
    predictedCategory.textContent = "-";

    showPage(imageUploadPage);
});


// 원형 버튼
recordButton.addEventListener("click", async () => {
    if (!isRecording) {
        try {
            const response = await fetch("/start-recording", {
                method: "POST"
            });

            const result = await response.json();

            if (!result.success) {
                alert(result.message || "녹음을 시작할 수 없습니다.");
                return;
            }

            isRecording = true;
            recordButton.classList.add("recording");
            recordButton.textContent = "⏹️";

            alert("녹음을 시작했습니다. 다시 버튼을 누르면 종료됩니다.");

        } catch (error) {
            alert("녹음 시작 중 오류가 발생했습니다.");
            console.error(error);
        }

    } else {
        try {
            recordButton.disabled = true;
            recordButton.textContent = "⏳";

            const response = await fetch("/stop-recording", {
                method: "POST"
            });

            const result = await response.json();

            if (!result.success) {
                alert(result.message || "녹음 처리에 실패했습니다.");
                return;
            }

            complaintText.value = result.raw_text;

            alert("음성 인식이 완료되었습니다. 변환하기 버튼을 눌러 주세요.");

        } catch (error) {
            alert("녹음 종료 또는 음성 처리 중 오류가 발생했습니다.");
            console.error(error);

        } finally {
            isRecording = false;
            recordButton.disabled = false;
            recordButton.classList.remove("recording");
            recordButton.textContent = "🎙️";
        }
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

    showPage(loadingPage);

    const formData = new FormData();
    formData.append("text", text);
    formData.append("image_category", selectedImageCategory);

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
            showPage(resultPage);

            finalText.textContent =
                `📌 문제상황\n${result.problem || "정보 없음"}\n\n` +
                `📍 위치\n${result.location || "정보 없음"}\n\n` +
                `📝 요구사항\n${result.request || "정보 없음"}\n\n` +
                `최종 민원문\n${result.final_text || ""}`;
            departmentResult.textContent = result.department;
        }, 1200);

    } catch (error) {
        alert("처리 중 오류가 발생했습니다.");
        console.error(error);

        showPage(inputPage);
    }
});


// 처음으로 버튼
restartButton.addEventListener("click", () => {
    complaintText.value = "";
    audioFile.value = "";
    complaintImage.value = "";
    imagePreviewWrap.classList.add("hidden");
    imagePreview.removeAttribute("src");
    predictedCategory.textContent = "-";
    selectedImageCategory = "";

    showPage(imageUploadPage);
});


let cropper;
const uploadInput = document.getElementById('profile-pic');
const previewImage = document.getElementById('preview-pic');
const modal = document.getElementById('cropModal');
const cropImage = document.getElementById('cropImage');
const closeModal = document.getElementById('closeModal');
const confirmCrop = document.getElementById('confirmCrop');
const deletePhotoBtn = document.getElementById('deletePhoto');
const cancelCropBtn = document.getElementById('cancelCrop');
const editPhotoBtn = document.getElementById('editPhoto');
const defaultImg = "/profpic/default.png";

function checkIfDefault() {
    if (previewImage.src.includes("default.png")) {
        editPhotoBtn.style.display = "none";
    }
}
checkIfDefault();

function openCropper(imageSrc) {
    cropImage.src = imageSrc;
    modal.style.display = 'block';
    if (cropper) cropper.destroy();
    cropper = new Cropper(cropImage, {
        aspectRatio: 1,
        viewMode: 1,
        movable: true,
        zoomable: true,
        background: false
    });
}

document.querySelector(".profile-pic-wrapper").addEventListener("click", function () {
    if (previewImage.src.includes("default.png")) return;
    if (previewImage.src.includes("{{user_profile_image}}")){ 
    openCropper("{{ user_profile_image }}");}
    openCropper(previewImage.src);
});


uploadInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => openCropper(reader.result);
    reader.readAsDataURL(file);
});

confirmCrop.addEventListener('click', () => {
    if (!cropper) return;

    cropper.getCroppedCanvas({ width: 300, height: 300 }).toBlob((blob) => {
        const file = new File([blob], "profile.png", { type: "image/png" });
        
    
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        uploadInput.files = dataTransfer.files;

        previewImage.src = URL.createObjectURL(file); 
        modal.style.display = 'none';
        cropper.destroy();
        cropper = null;
        editPhotoBtn.style.display = 'flex';
    }, "image/png");
});


deletePhotoBtn.addEventListener('click', () => {
    previewImage.src = defaultImg + "?t=" + Date.now();
    modal.style.display = 'none';
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
    uploadInput.value = "";
    editPhotoBtn.style.display = "none";
});

cancelCropBtn.addEventListener('click', () => {
    modal.style.display = 'none';
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
    uploadInput.value = "";
});

closeModal.addEventListener('click', () => {
    modal.style.display = 'none';
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
    uploadInput.value = "";
});

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.toggle-password').forEach(icon => {
        icon.addEventListener('click', function () {
            const input = this.parentElement.querySelector('input');
            if (input.type === 'password') {
                input.type = 'text';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
            }
        });
    });
});

function openDeleteModal() {
    document.getElementById('senha').value = '';
    document.getElementById('deleteModal').style.display = 'flex';
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

function confirmpass(event) {
    const senha = document.getElementById("senha").value.trim();
    if (!senha) {
        alert("Por favor, digite sua senha.");
        event.preventDefault();
        return false;
    }
    const confirmar = confirm("Tem certeza que deseja deletar sua conta?");
    if (!confirmar) {
        event.preventDefault();
        return false;
    }
    return true;
}
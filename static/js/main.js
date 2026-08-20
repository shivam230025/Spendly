// main.js — students will add JavaScript here as features are built

// ------------------------------------------------------------------ //
// "See how it works" video modal                                      //
// ------------------------------------------------------------------ //

(function () {
    // var YOUTUBE_EMBED_URL = "https://www.youtube.com/embed/dQw4w9WgXcQ";
    var YOUTUBE_EMBED_URL = "https://www.youtube.com/embed/dQw4w9WgXcQ";

    var trigger = document.getElementById("how-it-works-link");
    var overlay = document.getElementById("video-modal-overlay");
    var closeBtn = document.getElementById("video-modal-close");
    var iframe = document.getElementById("video-modal-iframe");

    if (!trigger || !overlay || !closeBtn || !iframe) return;

    function openModal(event) {
        event.preventDefault();
        iframe.src = YOUTUBE_EMBED_URL + "?autoplay=1";
        overlay.classList.add("is-open");
    }

    function closeModal() {
        overlay.classList.remove("is-open");
        iframe.src = "";
    }

    trigger.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);

    overlay.addEventListener("click", function (event) {
        if (event.target === overlay) closeModal();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && overlay.classList.contains("is-open")) closeModal();
    });
})();

// ------------------------------------------------------------------ //
// Confirm before deleting an expense                                  //
// ------------------------------------------------------------------ //

(function () {
    document.querySelectorAll(".delete-expense-form").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!window.confirm("Delete this expense? This cannot be undone.")) {
                event.preventDefault();
            }
        });
    });
})();

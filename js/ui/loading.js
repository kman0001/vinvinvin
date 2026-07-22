// ===========================
// loading
// ===========================

const startedAt = performance.now();

export function hideLoading(minDuration = 500) {

    const loading = document.getElementById("loading-screen");

    if (!loading) return;

    const elapsed = performance.now() - startedAt;
    const delay = Math.max(0, minDuration - elapsed);

    setTimeout(() => {

        loading.classList.add("hide");

        loading.addEventListener("transitionend", () => {
            loading.remove();
        }, { once: true });

    }, delay);

}

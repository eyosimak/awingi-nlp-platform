// Awingi NLP Platform — Global Client Script
document.addEventListener('DOMContentLoaded', () => {
    // Keyboard shortcuts for reviewer velocity
    document.addEventListener('keydown', (e) => {
        // Only trigger if no modal or input is currently focused
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
            return;
        }

        // 'A' key to approve first visible pending sentence
        if (e.key === 'a' || e.key === 'A') {
            const firstApproveForm = document.querySelector('form[action*="/approve"]');
            if (firstApproveForm) {
                firstApproveForm.submit();
            }
        }
    });
});

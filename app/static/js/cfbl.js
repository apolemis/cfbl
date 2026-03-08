/* ============================================
   cfbl.js — Tab switching, music, visitor counter
   xpage.com/cfbl
   ============================================ */

// Tab switching
document.querySelectorAll('.tab-btn[data-tab]').forEach(function(btn) {
    btn.addEventListener('click', function() {
        // Deactivate all tabs and content
        document.querySelectorAll('.tab-btn[data-tab]').forEach(function(b) {
            b.classList.remove('active');
        });
        document.querySelectorAll('.tab-content').forEach(function(c) {
            c.classList.remove('active');
        });
        // Activate clicked tab and its content
        btn.classList.add('active');
        var target = document.getElementById('tab-' + btn.getAttribute('data-tab'));
        if (target) target.classList.add('active');
    });
});

// Music player
var musicPlaying = false;
var audio = document.getElementById('island-audio');
var musicBtn = document.querySelector('.music-btn');

function toggleMusic() {
    if (!audio) return;
    if (musicPlaying) {
        audio.pause();
        if (musicBtn) {
            musicBtn.textContent = '\uD83C\uDFB5 Island Vibes \uD83C\uDFB5';
            musicBtn.classList.remove('playing');
        }
    } else {
        audio.volume = 0.3;
        audio.play().catch(function() {
            // Autoplay blocked — that's fine
        });
        if (musicBtn) {
            musicBtn.textContent = '\uD83D\uDD07 Stop Music';
            musicBtn.classList.add('playing');
        }
    }
    musicPlaying = !musicPlaying;
}

if (musicBtn) {
    musicBtn.addEventListener('click', toggleMusic);
}

// Fake visitor counter (persisted in localStorage)
(function() {
    var counterEl = document.getElementById('visitor-count');
    if (!counterEl) return;

    var count = parseInt(localStorage.getItem('cfbl_visitors') || '4207', 10);
    count += Math.floor(Math.random() * 3) + 1; // +1 to +3 each visit
    localStorage.setItem('cfbl_visitors', count.toString());

    // Format with leading zeros and commas
    var formatted = count.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    while (formatted.length < 7) formatted = '0' + formatted;
    counterEl.textContent = formatted;
})();

// Easter egg: Konami code plays a little alert
(function() {
    var konamiCode = [38,38,40,40,37,39,37,39,66,65];
    var konamiIndex = 0;
    document.addEventListener('keydown', function(e) {
        if (e.keyCode === konamiCode[konamiIndex]) {
            konamiIndex++;
            if (konamiIndex === konamiCode.length) {
                alert('YEAH MON! You found the secret! \uD83C\uDFDD\uFE0F\uD83E\uDD65');
                konamiIndex = 0;
            }
        } else {
            konamiIndex = 0;
        }
    });
})();

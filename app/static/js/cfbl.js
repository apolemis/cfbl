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

/* ============================================
   Salary Cap Tracker
   ============================================ */
(function() {
    if (typeof SALARY_CAP_DATA === 'undefined') return;

    var capData = SALARY_CAP_DATA;
    var rv = capData.round_values;

    // Compute current salary from trade history
    function computeSalary(team) {
        var salary = team.starting_salary;
        for (var i = 0; i < team.trades.length; i++) {
            var trade = team.trades[i];
            if (trade.gave) {
                for (var j = 0; j < trade.gave.length; j++) {
                    salary += rv[trade.gave[j] - 1];
                }
            }
            if (trade.got) {
                for (var j = 0; j < trade.got.length; j++) {
                    salary -= rv[trade.got[j] - 1];
                }
            }
        }
        return salary;
    }

    function getTeamById(id) {
        for (var i = 0; i < capData.teams.length; i++) {
            if (capData.teams[i].id === id) return capData.teams[i];
        }
        return null;
    }

    function pickValue(rd) {
        return rv[rd - 1];
    }

    function pickChipClass(rd) {
        var val = rv[rd - 1];
        if (val >= 14) return 'pick-chip-high';
        if (val >= 4) return 'pick-chip-mid';
        return 'pick-chip-low';
    }

    function capColorClass(salary) {
        if (salary > capData.cap_ceiling) return 'cap-red';
        if (salary > capData.cap_ceiling - 30) return 'cap-yellow';
        if (salary < capData.cap_floor) return 'cap-red';
        if (salary < capData.cap_floor + 20) return 'cap-yellow';
        return 'cap-green';
    }

    // Populate overview table
    function refreshOverview() {
        for (var i = 0; i < capData.teams.length; i++) {
            var team = capData.teams[i];
            var salary = computeSalary(team);
            var room = capData.cap_ceiling - salary;

            var currentEl = document.getElementById('cap-current-' + team.id);
            var roomEl = document.getElementById('cap-room-' + team.id);
            var countEl = document.getElementById('cap-picks-count-' + team.id);

            if (currentEl) {
                currentEl.textContent = '$' + salary;
                currentEl.className = 'cap-current ' + capColorClass(salary);
            }
            if (roomEl) {
                roomEl.textContent = '$' + room;
                roomEl.className = 'cap-room ' + capColorClass(salary);
            }
            if (countEl) {
                countEl.textContent = team.picks.length;
            }

            // Update pick inventory if visible
            var invEl = document.getElementById('pick-inventory-' + team.id);
            if (invEl) {
                renderPickInventory(team, invEl);
            }
        }
    }

    function renderPickInventory(team, container) {
        var html = '';
        var picks = team.picks.slice().sort(function(a, b) { return a - b; });
        for (var i = 0; i < picks.length; i++) {
            var rd = picks[i];
            html += '<span class="pick-chip ' + pickChipClass(rd) + '">Rd ' + rd + ' ($' + pickValue(rd) + ')</span>';
        }
        if (picks.length === 0) {
            html = '<span style="color:#888;font-style:italic;">No picks</span>';
        }
        container.innerHTML = html;
    }

    // Toggle pick inventory row
    window.togglePickInventory = function(teamId) {
        var row = document.getElementById('cap-picks-row-' + teamId);
        if (!row) return;
        if (row.style.display === 'none') {
            row.style.display = '';
            var team = getTeamById(teamId);
            var inv = document.getElementById('pick-inventory-' + teamId);
            if (team && inv) renderPickInventory(team, inv);
        } else {
            row.style.display = 'none';
        }
    };

    // Trade simulator
    function getSelectedPicks(side) {
        var container = document.getElementById('trade-picks-' + side);
        if (!container) return [];
        var checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
        var picks = [];
        for (var i = 0; i < checkboxes.length; i++) {
            picks.push(parseInt(checkboxes[i].value, 10));
        }
        return picks;
    }

    function renderPickList(team, containerId) {
        var container = document.getElementById(containerId);
        if (!container) return;
        if (!team) {
            container.innerHTML = '<span style="color:#666;font-size:11px;">Select a team</span>';
            return;
        }
        var picks = team.picks.slice().sort(function(a, b) { return a - b; });
        var html = '';
        for (var i = 0; i < picks.length; i++) {
            var rd = picks[i];
            html += '<label class="trade-pick-item">';
            html += '<input type="checkbox" value="' + rd + '" onchange="onPickToggle()"> ';
            html += 'Rd ' + rd + ' &mdash; $' + pickValue(rd);
            html += '</label>';
        }
        container.innerHTML = html;
    }

    window.onTradeTeamSelect = function() {
        var aId = parseInt(document.getElementById('trade-team-a').value, 10);
        var bId = parseInt(document.getElementById('trade-team-b').value, 10);

        var teamA = getTeamById(aId);
        var teamB = getTeamById(bId);

        renderPickList(teamA, 'trade-picks-a');
        renderPickList(teamB, 'trade-picks-b');

        updateTradeSummaries();
        clearTradeResults();
    };

    window.onPickToggle = function() {
        updateTradeSummaries();
        clearTradeResults();
    };

    function updateTradeSummaries() {
        var aId = parseInt(document.getElementById('trade-team-a').value, 10);
        var bId = parseInt(document.getElementById('trade-team-b').value, 10);
        var teamA = getTeamById(aId);
        var teamB = getTeamById(bId);

        var picksA = getSelectedPicks('a');
        var picksB = getSelectedPicks('b');

        var summA = document.getElementById('trade-summary-a');
        var summB = document.getElementById('trade-summary-b');
        var validation = document.getElementById('trade-validation');

        if (summA) {
            if (teamA && picksA.length > 0) {
                var val = 0;
                for (var i = 0; i < picksA.length; i++) val += pickValue(picksA[i]);
                summA.innerHTML = 'Giving away: ' + picksA.length + ' pick(s), $' + val + ' total value';
            } else {
                summA.innerHTML = '';
            }
        }

        if (summB) {
            if (teamB && picksB.length > 0) {
                var val = 0;
                for (var i = 0; i < picksB.length; i++) val += pickValue(picksB[i]);
                summB.innerHTML = 'Giving away: ' + picksB.length + ' pick(s), $' + val + ' total value';
            } else {
                summB.innerHTML = '';
            }
        }

        // Validation
        if (validation) {
            if (picksA.length === 0 && picksB.length === 0) {
                validation.className = 'trade-validation';
                validation.innerHTML = '';
            } else if (picksA.length !== picksB.length) {
                validation.className = 'trade-validation error';
                validation.innerHTML = '\u26A0 Must exchange equal number of picks (' + picksA.length + ' vs ' + picksB.length + ')';
            } else {
                validation.className = 'trade-validation valid';
                validation.innerHTML = '\u2705 ' + picksA.length + ' pick(s) per side — ready to simulate';
            }
        }
    }

    function clearTradeResults() {
        var results = document.getElementById('trade-results');
        var execBtn = document.getElementById('execute-btn');
        if (results) results.style.display = 'none';
        if (execBtn) execBtn.disabled = true;
    }

    window.simulateTrade = function() {
        var aId = parseInt(document.getElementById('trade-team-a').value, 10);
        var bId = parseInt(document.getElementById('trade-team-b').value, 10);
        var teamA = getTeamById(aId);
        var teamB = getTeamById(bId);

        if (!teamA || !teamB) {
            showValidation('Select both teams', true);
            return;
        }
        if (aId === bId) {
            showValidation('Cannot trade with yourself', true);
            return;
        }

        var picksA = getSelectedPicks('a');
        var picksB = getSelectedPicks('b');

        if (picksA.length === 0 || picksB.length === 0) {
            showValidation('Select picks for both teams', true);
            return;
        }
        if (picksA.length !== picksB.length) {
            showValidation('Must exchange equal number of picks (' + picksA.length + ' vs ' + picksB.length + ')', true);
            return;
        }

        var salA = computeSalary(teamA);
        var salB = computeSalary(teamB);

        var aGivesVal = 0, aGetsVal = 0;
        for (var i = 0; i < picksA.length; i++) aGivesVal += pickValue(picksA[i]);
        for (var i = 0; i < picksB.length; i++) aGetsVal += pickValue(picksB[i]);

        var newSalA = salA + aGivesVal - aGetsVal;
        var newSalB = salB + aGetsVal - aGivesVal;

        var results = document.getElementById('trade-results');
        var content = document.getElementById('trade-results-content');
        var execBtn = document.getElementById('execute-btn');

        var errors = [];
        if (newSalA > capData.cap_ceiling) errors.push(teamA.owner + ' exceeds cap ceiling ($' + newSalA + ' > $' + capData.cap_ceiling + ')');
        if (newSalA < capData.cap_floor) errors.push(teamA.owner + ' below cap floor ($' + newSalA + ' < $' + capData.cap_floor + ')');
        if (newSalB > capData.cap_ceiling) errors.push(teamB.owner + ' exceeds cap ceiling ($' + newSalB + ' > $' + capData.cap_ceiling + ')');
        if (newSalB < capData.cap_floor) errors.push(teamB.owner + ' below cap floor ($' + newSalB + ' < $' + capData.cap_floor + ')');

        var html = '';
        html += '<div class="trade-results-line"><strong>' + teamA.owner + ':</strong> $' + salA + ' \u2192 <span class="' + capColorClass(newSalA) + '">$' + newSalA + '</span>';
        html += ' (gives Rd ' + picksA.join(', Rd ') + ' / gets Rd ' + picksB.join(', Rd ') + ')</div>';
        html += '<div class="trade-results-line"><strong>' + teamB.owner + ':</strong> $' + salB + ' \u2192 <span class="' + capColorClass(newSalB) + '">$' + newSalB + '</span>';
        html += ' (gives Rd ' + picksB.join(', Rd ') + ' / gets Rd ' + picksA.join(', Rd ') + ')</div>';

        if (errors.length > 0) {
            html += '<div style="color:#FF4444;margin-top:8px;">\u274C ILLEGAL: ' + errors.join('; ') + '</div>';
            if (execBtn) execBtn.disabled = true;
        } else {
            html += '<div style="color:#00FF00;margin-top:8px;">\u2705 Trade is legal!</div>';
            if (execBtn) execBtn.disabled = false;
        }

        if (content) content.innerHTML = html;
        if (results) results.style.display = 'block';
    };

    window.executeTrade = function() {
        var aId = parseInt(document.getElementById('trade-team-a').value, 10);
        var bId = parseInt(document.getElementById('trade-team-b').value, 10);
        var picksA = getSelectedPicks('a');
        var picksB = getSelectedPicks('b');

        fetch('/api/trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                team_a_id: aId,
                team_b_id: bId,
                team_a_gives: picksA,
                team_b_gives: picksB
            })
        })
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            if (data.error) {
                showValidation(data.error, true);
                return;
            }
            // Update local data
            var teamA = getTeamById(aId);
            var teamB = getTeamById(bId);
            if (teamA && teamB) {
                for (var i = 0; i < picksA.length; i++) {
                    var idx = teamA.picks.indexOf(picksA[i]);
                    if (idx > -1) teamA.picks.splice(idx, 1);
                    teamB.picks.push(picksA[i]);
                }
                for (var i = 0; i < picksB.length; i++) {
                    var idx = teamB.picks.indexOf(picksB[i]);
                    if (idx > -1) teamB.picks.splice(idx, 1);
                    teamA.picks.push(picksB[i]);
                }
                teamA.picks.sort(function(a, b) { return a - b; });
                teamB.picks.sort(function(a, b) { return a - b; });
                teamA.trades.push({ gave: picksA, got: picksB, 'with': teamB.owner });
                teamB.trades.push({ gave: picksB, got: picksA, 'with': teamA.owner });
            }

            refreshOverview();
            resetTrade();
            showValidation('\u2705 Trade executed! Remember to process on Yahoo.', false);
            refreshTradeHistory();
        })
        .catch(function(err) {
            showValidation('Error: ' + err.message, true);
        });
    };

    window.resetTrade = function() {
        document.getElementById('trade-team-a').value = '';
        document.getElementById('trade-team-b').value = '';
        document.getElementById('trade-picks-a').innerHTML = '<span style="color:#666;font-size:11px;">Select a team</span>';
        document.getElementById('trade-picks-b').innerHTML = '<span style="color:#666;font-size:11px;">Select a team</span>';
        document.getElementById('trade-summary-a').innerHTML = '';
        document.getElementById('trade-summary-b').innerHTML = '';
        document.getElementById('trade-validation').className = 'trade-validation';
        document.getElementById('trade-validation').innerHTML = '';
        clearTradeResults();
    };

    window.undoLastTrade = function() {
        fetch('/api/undo-trade', { method: 'POST' })
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            if (data.error) {
                showValidation(data.error, true);
                return;
            }
            // Reload page to get fresh data
            window.location.reload();
        })
        .catch(function(err) {
            showValidation('Error: ' + err.message, true);
        });
    };

    function showValidation(msg, isError) {
        var el = document.getElementById('trade-validation');
        if (!el) return;
        el.className = 'trade-validation ' + (isError ? 'error' : 'valid');
        el.innerHTML = msg;
    }

    function refreshTradeHistory() {
        var container = document.getElementById('trade-history');
        if (!container) return;

        var allTrades = [];
        for (var i = 0; i < capData.teams.length; i++) {
            var team = capData.teams[i];
            for (var j = 0; j < team.trades.length; j++) {
                var t = team.trades[j];
                // Deduplicate: only show from the perspective of the team with lower id
                var partnerId = 0;
                for (var k = 0; k < capData.teams.length; k++) {
                    if (capData.teams[k].owner === t['with']) { partnerId = capData.teams[k].id; break; }
                }
                if (team.id < partnerId) {
                    allTrades.push({
                        teamA: team.owner,
                        teamB: t['with'],
                        aGave: t.gave,
                        aGot: t.got
                    });
                }
            }
        }

        if (allTrades.length === 0) {
            container.innerHTML = '<p class="no-trades">No trades have been executed yet. The island is quiet\u2026 for now.</p>';
            return;
        }

        var html = '<div id="trade-history-list">';
        for (var i = 0; i < allTrades.length; i++) {
            var tr = allTrades[i];
            html += '<div class="trade-history-item">';
            html += '<strong>' + tr.teamA + '</strong> sends Rd ' + tr.aGave.join(', Rd ');
            html += ' \u2194 <strong>' + tr.teamB + '</strong> sends Rd ' + tr.aGot.join(', Rd ');
            html += '</div>';
        }
        html += '</div>';
        container.innerHTML = html;
    }

    // Initialize
    refreshOverview();
    refreshTradeHistory();
})();

let matchData = JSON.parse(localStorage.getItem("matchData")) || {
  score: 0, wickets: 0, balls: [], currentBall: 0,
  players: {}, bowlers: {}, batterHistory: [], bowlerHistory: [],
  team1: "Team A", team2: "Team B", totalOvers: 20, ballType: "Tennis", city: "Unknown",
  battingTeam: "Team A", openingPair: { striker: "Player 1", nonStriker: "Player 2" }, currentBowler: "Bowler 1"
};

function updateLocalStorage() {
  localStorage.setItem("matchData", JSON.stringify(matchData));
}

function showTab(tabId, event) {
  document.querySelectorAll(".tab-content").forEach(tab => tab.classList.remove("active"));
  document.querySelectorAll(".tab-button").forEach(btn => btn.classList.remove("active"));
  document.getElementById(tabId).classList.add("active");
  event.target.classList.add("active");
}

function toggleExtraFields() {
  const extra = document.getElementById("extraInput").value;
  document.getElementById("extraRunInput").classList.toggle("hidden", extra === "");
  document.getElementById("batHitLabel").classList.toggle("hidden", extra !== "no-ball");
}

function recordBall() {
  const run = parseInt(document.getElementById("runInput").value);
  const extra = document.getElementById("extraInput").value;
  const extraRuns = parseInt(document.getElementById("extraRunInput").value || 0);
  const batHit = document.getElementById("batHitCheckbox").checked;
  const striker = matchData.openingPair.striker;
  const bowler = matchData.currentBowler;

  matchData.balls.push(extra ? (extra === "wide" ? `WD+${extraRuns}` : `NB+${extraRuns}`) : run.toString());
  matchData.score += run + (extra ? 1 + extraRuns : 0);

  matchData.players[striker] = matchData.players[striker] || { runs: 0, balls: 0, fours: 0, sixes: 0 };
  if (!extra || (extra === "no-ball" && batHit)) {
    matchData.players[striker].runs += run;
    matchData.players[striker].balls++;
    if (run === 4) matchData.players[striker].fours++;
    if (run === 6) matchData.players[striker].sixes++;
  }

  matchData.bowlers[bowler] = matchData.bowlers[bowler] || { balls: 0, runs: 0, wickets: 0 };
  matchData.bowlers[bowler].runs += run + (extra ? 1 + extraRuns : 0);
  if (!extra) {
    matchData.bowlers[bowler].balls++;
    matchData.currentBall++;

    if (matchData.currentBall % 6 === 0) {
      saveOverSnapshot();
      openBowlerModal();
    }
  }

  updateLocalStorage();
  updateUI();
}

function saveOverSnapshot() {
  const striker = matchData.openingPair.striker;
  const bowler = matchData.currentBowler;

  matchData.batterHistory.push({
    over: Math.floor(matchData.currentBall / 6),
    batsman: striker,
    stats: { ...matchData.players[striker] }
  });

  matchData.bowlerHistory.push({
    over: Math.floor(matchData.currentBall / 6),
    bowler: bowler,
    stats: { ...matchData.bowlers[bowler] }
  });
}

function openBowlerModal() {
  const modal = document.getElementById("bowlerModal");
  const select = document.getElementById("bowlerSelect");
  select.innerHTML = "";

  const existing = Object.keys(matchData.bowlers);
  const options = new Set([...existing, "Bowler 1", "Bowler 2", "Bowler 3", "Bowler 4"]);

  for (let name of options) {
    const opt = document.createElement("option");
    opt.value = opt.text = name;
    select.appendChild(opt);
  }

  modal.style.display = "block";
}

function confirmBowlerChange() {
  const selected = document.getElementById("bowlerSelect").value;
  if (selected) {
    matchData.currentBowler = selected;
    matchData.bowlers[selected] = matchData.bowlers[selected] || { balls: 0, runs: 0, wickets: 0 };
    updateLocalStorage();
    updateUI();
  }
  document.getElementById("bowlerModal").style.display = "none";
}

window.onclick = function(event) {
  const modal = document.getElementById("bowlerModal");
  if (event.target === modal) {
    modal.style.display = "none";
  }
};

function updateUI() {
  const overs = `${Math.floor(matchData.currentBall / 6)}.${matchData.currentBall % 6}`;
  document.getElementById("matchTitle").innerText = `${matchData.team1} vs ${matchData.team2}`;
  document.getElementById("matchMeta").innerText = `${matchData.totalOvers} Overs • ${matchData.ballType} • ${matchData.city}`;
  document.getElementById("battingTeamScore").innerText = `${matchData.battingTeam} ${matchData.score}/${matchData.wickets} (${overs})`;
  document.getElementById("targetInfo").innerText = `Target 130 • Need ${130 - matchData.score} from ${120 - matchData.currentBall} balls`;

  const striker = matchData.openingPair.striker;
  const nonStriker = matchData.openingPair.nonStriker;

  const batterRows = [striker, nonStriker].map(name => {
    const b = matchData.players[name] || { runs: 0, balls: 0, fours: 0, sixes: 0 };
    const sr = b.balls ? ((b.runs / b.balls) * 100).toFixed(1) : "0.0";
    return `<tr><td class="highlight">${name}</td><td>${b.runs}</td><td>${b.balls}</td><td>${b.fours}</td><td>${b.sixes}</td><td>${sr}</td></tr>`;
  }).join('');
  document.querySelector("#battersTable tbody").innerHTML = batterRows;

  const bStat = matchData.bowlers[matchData.currentBowler] || { balls: 0, runs: 0, wickets: 0 };
  const oversBowled = `${Math.floor(bStat.balls / 6)}.${bStat.balls % 6}`;
  const econ = bStat.balls ? (bStat.runs / (bStat.balls / 6)).toFixed(2) : "0.00";
  document.querySelector("#bowlerTable tbody").innerHTML = `<tr><td>${matchData.currentBowler}</td><td>${oversBowled}</td><td>${bStat.runs}</td><td>${bStat.wickets}</td><td>${econ}</td></tr>`;

  const lastBalls = matchData.balls.slice(-6).reverse();
  document.getElementById("lastBalls").innerHTML = lastBalls.map(b => {
    let cls = "ball";
    if (b.includes("W")) cls += " w";
    else if (b.includes("4")) cls += " r4";
    else if (b.includes("6")) cls += " r6";
    else if (b.startsWith("WD") || b.startsWith("NB")) cls += " extra";
    return `<div class="${cls}">${b}</div>`;
  }).join('');

  updateFullScorecard();
}

function updateFullScorecard() {
  const batters = Object.entries(matchData.players || {}).map(([name, b]) => {
    const sr = b.balls ? ((b.runs / b.balls) * 100).toFixed(1) : "0.0";
    return `<tr><td>${name}</td><td>${b.runs}</td><td>${b.balls}</td><td>${b.fours}</td><td>${b.sixes}</td><td>${sr}</td></tr>`;
  }).join('');
  document.querySelector("#fullBattersTable tbody").innerHTML = batters;

  const bowlers = Object.entries(matchData.bowlers || {}).map(([name, b]) => {
    const overs = `${Math.floor(b.balls / 6)}.${b.balls % 6}`;
    const econ = b.balls ? (b.runs / (b.balls / 6)).toFixed(2) : "0.00";
    return `<tr><td>${name}</td><td>${overs}</td><td>${b.runs}</td><td>${b.wickets}</td><td>${econ}</td></tr>`;
  }).join('');
  document.querySelector("#fullBowlerTable tbody").innerHTML = bowlers;

  const bhist = matchData.batterHistory.map(entry => {
    const b = entry.stats;
    return `<tr><td>${entry.over}</td><td>${entry.batsman}</td><td>${b.runs}</td><td>${b.balls}</td><td>${b.fours}</td><td>${b.sixes}</td></tr>`;
  }).join('');
  document.querySelector("#batterHistory tbody").innerHTML = bhist;

  const whist = matchData.bowlerHistory.map(entry => {
    const b = entry.stats;
    const overs = `${Math.floor(b.balls / 6)}.${b.balls % 6}`;
    return `<tr><td>${entry.over}</td><td>${entry.bowler}</td><td>${overs}</td><td>${b.runs}</td><td>${b.wickets}</td></tr>`;
  }).join('');
  document.querySelector("#bowlerHistory tbody").innerHTML = whist;
}

updateUI();

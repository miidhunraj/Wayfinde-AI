let currentState = null;
let latestPlanId = null;
const $ = (id) => document.getElementById(id);

function money(value) {
  const sign = value < 0 ? "−" : "";
  return sign + "₹" + Math.abs(Number(value || 0)).toLocaleString("en-IN");
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function toast(message, error=false) {
  const el = $("toast"); el.textContent = message; el.className = "toast show" + (error ? " error" : "");
  setTimeout(() => el.className = "toast", 3200);
}
function scrollToSection(id) { $(id).scrollIntoView({behavior:"smooth", block:"start"}); }
function statusLabel(status) {
  return ({confirmed:"Confirmed", disrupted:"Disrupted", recovery_accepted_demo:"Plan accepted (demo)", cancelled:"Cancelled"})[status] || status;
}
function iconFor(type) { return ({flight:"✈",train:"▰",hotel:"⌂"})[type] || "•"; }
function routeFor(b) { return b.type === "hotel" ? b.city : `${b.from} → ${b.to}`; }
function dateLabel(date) { return new Date(date+"T12:00:00").toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric"}); }

async function refreshState() {
  const response = await fetch("/api/state");
  currentState = await response.json();
  render();
}
function render() {
  if (!currentState) return;
  const bookings = currentState.bookings;
  $("stat-bookings").textContent = bookings.filter(b => b.status !== "cancelled").length;
  $("booking-count").textContent = bookings.length;
  $("stat-disruptions").textContent = currentState.disruptions.filter(d => d.status !== "resolved").length;
  $("stat-plans").textContent = currentState.recovery_plans.length;
  $("stat-savings").textContent = "₹0";
  $("disruption-total").textContent = `${currentState.disruptions.length} event${currentState.disruptions.length === 1 ? "" : "s"}`;
  const firstTrip = bookings.find(b => b.traveller === currentState.traveller.name);
  if (firstTrip) {
    $("journey-date").textContent = dateLabel(firstTrip.date);
    if (!$("date").value) $("date").value = firstTrip.date;
  }
  $("booking-list").innerHTML = bookings.map(b => `
    <div class="booking-row">
      <div class="booking-icon ${b.type}">${iconFor(b.type)}</div>
      <div class="booking-main"><strong>${escapeHtml(b.type[0].toUpperCase()+b.type.slice(1))} · ${escapeHtml(routeFor(b))}</strong><p>${escapeHtml(b.provider)} · ${escapeHtml(dateLabel(b.date))}${b.departure ? " · "+escapeHtml(b.departure) : ""}</p><div class="booking-ref">Ref ${escapeHtml(b.reference)} · ${escapeHtml(b.id)}</div></div>
      <div class="booking-right"><div class="booking-price">${money(b.price)}</div><span class="pill ${escapeHtml(b.status)}">${escapeHtml(statusLabel(b.status))}</span></div>
    </div>`).join("");
  renderDisruptions();
  renderPlans();
}
function renderDisruptions() {
  const list = $("disruption-list");
  if (!currentState.disruptions.length) {
    list.innerHTML = `<div class="empty-state"><div class="empty-symbol">⌁</div><strong>All clear for now</strong><p>Simulate a disruption above to see the recovery workflow.</p></div>`;
    return;
  }
  list.innerHTML = currentState.disruptions.map(d => `
    <div class="event-row">
      <div class="event-symbol">${iconFor(d.type)}</div>
      <div class="event-main"><strong>${escapeHtml(d.type[0].toUpperCase()+d.type.slice(1))} ${escapeHtml(d.from ? d.from+" → "+d.to : "in "+d.city)} · ${escapeHtml(d.reason)}</strong><p>${escapeHtml(dateLabel(d.date))} · ${d.affected_booking_ids.length} affected booking(s) · ${escapeHtml(d.id)}</p></div>
      <div class="event-meta"><small>${escapeHtml(d.status.replaceAll("_"," "))}</small><button onclick="buildRecovery('${escapeHtml(d.id)}')">Build recovery plan ↗</button></div>
    </div>`).join("");
}
function renderPlans() {
  const target = $("recovery-list");
  if (!currentState.recovery_plans.length) {
    target.innerHTML = `<div class="empty-state compact"><div class="empty-symbol">✧</div><strong>Your recovery plan will appear here</strong><p>Detect a disruption, then select “Build recovery plan”.</p></div>`;
    return;
  }
  target.innerHTML = currentState.recovery_plans.map(plan => `
    <div class="recovery-plan">
      <div class="plan-head"><div><strong>Recovery proposal · ${escapeHtml(plan.id)}</strong><small>Created ${escapeHtml(plan.created_at.replace("T"," "))} · ${escapeHtml(plan.status.replaceAll("_"," "))}</small></div><span class="pill ${plan.status === "accepted_demo" ? "recovery_accepted_demo" : "confirmed"}">${plan.status === "accepted_demo" ? "Accepted in demo" : "Proposed"}</span></div>
      <div class="plan-summary">${escapeHtml(plan.summary)}</div>
      ${plan.items.map(item => `
        <div class="plan-item">
          <div class="plan-item-head"><div><strong>${escapeHtml(item.booking_type.toUpperCase())} · ${escapeHtml(routeFor(item.original))}</strong><p>Original: ${escapeHtml(item.original.provider)} · ${money(item.original.price)}</p></div><span class="pill ${item.recommended ? "confirmed" : "disrupted"}">${item.recommended ? "Alternative found" : "Needs attention"}</span></div>
          ${item.recommended ? `<div class="recommendation"><div class="rec-kicker">✦ BEST MATCH · SIMULATED DEMO OPTION</div><strong>${escapeHtml(item.recommended.service_name || item.recommended.provider)} · ${money(item.recommended.price)}</strong><p>${escapeHtml(item.recommended.note)}<br>${item.recommended.type === "hotel" ? "Check-in/out: " + escapeHtml(item.recommended.check_in || "") + " / " + escapeHtml(item.recommended.check_out || "") : "Service: " + escapeHtml(item.recommended.service_number || "") + " · Time: " + escapeHtml(item.recommended.departure || "") + "–" + escapeHtml(item.recommended.arrival || "")}</p><p><b>Original booking:</b> ${money(item.original.price)} · <b>Alternative price:</b> ${money(item.recommended.price)} · <b>Difference:</b> <span class="rec-price">${money(item.recommended.extra_cost)}</span></p><p><b>Why it fits:</b> ${escapeHtml(item.recommended.reason)}</p></div>
          ${item.alternatives.length ? `<div class="option-list"><div class="rec-kicker">OTHER ALTERNATIVES · ${item.alternatives.length} OPTIONS</div>${item.alternatives.map((alt, index) => `<div class="option-row"><div><strong>${index === 0 ? "Recommended · " : ""}${escapeHtml(alt.service_name || alt.provider)} · ${money(alt.price)}</strong><p>${escapeHtml(alt.note)} · Original fare: ${money(item.original.price)} · Difference: ${money(alt.extra_cost)}</p><p>${alt.type === "hotel" ? "Check-in/out: " + escapeHtml(alt.check_in || "") + " / " + escapeHtml(alt.check_out || "") : "Service " + escapeHtml(alt.service_number || "") + " · " + escapeHtml(alt.departure || "") + "–" + escapeHtml(alt.arrival || "")}</p></div><span>${alt.price_match ? "Same price" : "Price differs"}</span></div>`).join("")}</div><p class="plan-warning">Illustrative demo data only. Provider names, service numbers, schedules, rooms and availability are not verified live.</p>` : ""}`
          : `<p style="font-size:10px;color:#b16b25;margin-top:10px">${escapeHtml(item.action_required)}</p>`}
        </div>`).join("")}
      <div class="plan-actions"><button class="button button-primary" onclick="acceptPlan('${escapeHtml(plan.id)}')" ${plan.status === "accepted_demo" ? "disabled" : ""}>Accept proposal (demo)</button><button class="button-outline" onclick="copyPlan('${escapeHtml(plan.id)}')">Copy itinerary</button><span class="plan-warning">Demo only — no provider is contacted and no booking is made.</span></div>
    </div>`).join("");
}
function syncTypeFields() {
  const type = document.querySelector('input[name="type"]:checked').value;
  $("city-field").hidden = type !== "hotel";
  $("from").parentElement.parentElement.hidden = type === "hotel";
}
document.querySelectorAll('input[name="type"]').forEach(el => el.addEventListener("change", syncTypeFields));
syncTypeFields();

$("disruption-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const type = document.querySelector('input[name="type"]:checked').value;
  const payload = {type, date:$("date").value, reason:$("reason").value};
  if (type === "hotel") payload.city = $("city").value;
  else { payload.from = $("from").value; payload.to = $("to").value; }
  try {
    const response = await fetch("/api/disruptions", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not create disruption.");
    await refreshState();
    toast(`Disruption detected. ${result.affected_count} booking(s) matched.`);
    scrollToSection("disruptions");
  } catch (e) { toast(e.message, true); }
});

async function buildRecovery(id) {
  try {
    const response = await fetch(`/api/recover/${encodeURIComponent(id)}`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({max_extra_budget:4500,arrival_tolerance_hours:5,avoid_overnight:true})});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not build plan.");
    latestPlanId = result.plan.id;
    await refreshState();
    toast("Recovery proposal generated from your demo constraints.");
    scrollToSection("recovery");
  } catch (e) { toast(e.message, true); }
}
async function acceptPlan(id) {
  try {
    const response = await fetch(`/api/confirm/${encodeURIComponent(id)}`, {method:"POST"});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not accept proposal.");
    await refreshState();
    toast(result.message);
  } catch (e) { toast(e.message, true); }
}
function copyPlan(id) {
  const plan = currentState.recovery_plans.find(p => p.id === id);
  if (!plan) return;
  const lines = [`WAYFINDER AI — RECOVERY ITINERARY ${plan.id}`, plan.summary, ""];
  for (const item of plan.items) {
    lines.push(`${item.booking_type.toUpperCase()} ${routeFor(item.original)} (${item.booking_id})`);
    lines.push(item.recommended ? `Suggested: ${item.recommended.provider} · ${money(item.recommended.price)} · Extra ${money(item.recommended.extra_cost)}` : "Action: contact provider; no option matched current constraints.");
    if (item.recommended) lines.push(`Reason: ${item.recommended.reason}`);
    lines.push(`Action required: ${item.action_required}`, "");
  }
  lines.push("Demo proposal only; no booking or payment was made.");
  const text = lines.join("\n");
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(() => toast("Itinerary copied to clipboard.")).catch(() => fallbackCopy(text));
  else fallbackCopy(text);
}
function fallbackCopy(text) {
  const area = document.createElement("textarea"); area.value = text; document.body.appendChild(area); area.select();
  try { document.execCommand("copy"); toast("Itinerary copied to clipboard."); } catch(e) { toast("Copy failed. Please select and copy manually.", true); }
  area.remove();
}
async function resetDemo() {
  if (!confirm("Reset all demo bookings, disruptions and recovery plans?")) return;
  const response = await fetch("/api/reset", {method:"POST"});
  if (response.ok) { await refreshState(); toast("Demo data reset."); }
}
refreshState().catch(() => toast("Unable to load app state. Is the server running?", true));

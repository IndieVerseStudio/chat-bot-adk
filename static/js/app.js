const sessionId = Math.random().toString().substring(10);
const ws_url = "wss://" + window.location.host + "/ws/" + sessionId;
let websocket = null;
let promptSent = false;

function connectWebsocket() {
  websocket = new WebSocket(ws_url);

  // websocket.onopen = function () {
  //   console.log("WebSocket connection opened.");
  // };

  websocket.onmessage = function (event) {
    const message_from_server = JSON.parse(event.data);
    console.log("[AGENT TO CLIENT] ", message_from_server);

    // Handle instruction update response
    if (message_from_server.type === "instruction_updated") {
      console.log("Agent instructions updated successfully");
      promptSent = true;
      updateStatus(
        "Prompt set successfully! You can now start talking.",
        "conversation-ready"
      );
      enableStartButton();
      return;
    }

    if (
      message_from_server.turn_complete &&
      message_from_server.turn_complete == true
    ) {
      return;
    }

    if (
      message_from_server.interrupted &&
      message_from_server.interrupted === true
    ) {
      if (audioPlayerNode) {
        audioPlayerNode.port.postMessage({ command: "endOfAudio" });
      }
      return;
    }

    if (message_from_server.mime_type == "audio/pcm" && audioPlayerNode) {
      audioPlayerNode.port.postMessage(base64ToArray(message_from_server.data));
    }
  };

  websocket.onclose = function () {
    console.log("WebSocket connection closed.");
    setTimeout(function () {
      console.log("Reconnecting...");
      connectWebsocket();
    }, 5000);
  };

  websocket.onerror = function (e) {
    console.log("WebSocket error: ", e);
  };
}
// connectWebsocket();

function sendMessage(message) {
  if (websocket && websocket.readyState == WebSocket.OPEN) {
    const messageJson = JSON.stringify(message);
    websocket.send(messageJson);
  }
}

function updateStatus(message, className = "") {
  const statusText = document.getElementById("statusText");
  statusText.textContent = message;
  statusText.className = "status-text " + className;
}

function enableStartButton() {
  const startButton = document.getElementById("startAudioButton");
  startButton.disabled = false;
}

function disableStartButton() {
  const startButton = document.getElementById("startAudioButton");
  startButton.disabled = true;
}

// Decode Base64 data to Array
function base64ToArray(base64) {
  const binaryString = window.atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Audio handling
 */

let audioPlayerNode;
let audioPlayerContext;
let audioRecorderNode;
let audioRecorderContext;
let micStream;

// Audio buffering for 0.2s intervals
let audioBuffer = [];
let bufferTimer = null;

// Import the audio worklets
import { startAudioPlayerWorklet } from "./audio-player.js";
import { startAudioRecorderWorklet } from "./audio-recorder.js";

// Start audio
function startAudio() {
  // Start audio output
  startAudioPlayerWorklet().then(([node, ctx]) => {
    audioPlayerNode = node;
    audioPlayerContext = ctx;
  });
  // Start audio input
  startAudioRecorderWorklet(audioRecorderHandler).then(
    ([node, ctx, stream]) => {
      audioRecorderNode = node;
      audioRecorderContext = ctx;
      micStream = stream;
    }
  );
}

// Get DOM elements
const startAudioButton = document.getElementById("startAudioButton");
const sendPromptButton = document.getElementById("sendPromptButton");
const customPromptTextarea = document.getElementById("customPrompt");

// Handle prompt sending
sendPromptButton.addEventListener("click", () => {
  const customPrompt = customPromptTextarea.value.trim();

  if (!websocket || websocket.readyState !== WebSocket.OPEN) {
    // Connect first if not connected
    connectWebsocket();

    // Wait for connection to be established
    websocket.onopen = function () {
      sendCustomPrompt(customPrompt);
    };
  } else {
    sendCustomPrompt(customPrompt);
  }
});

function sendCustomPrompt(prompt) {
  sendPromptButton.disabled = true;
  updateStatus("Setting prompt...", "");

  const message = {
    type: "update_instruction",
    instruction: prompt || null, // Send null if empty to use default
  };

  sendMessage(message);
}

// Start the audio only when the user clicked the button
// (due to the gesture requirement for the Web Audio API)
startAudioButton.addEventListener("click", () => {
  if (!promptSent) {
    updateStatus(
      "Please set a prompt first before starting the conversation.",
      ""
    );
    return;
  }

  startAudioButton.disabled = true;
  startAudio();
  updateStatus("Starting conversation...", "");
});

// Audio recorder handler
function audioRecorderHandler(pcmData) {
  // Add audio data to buffer
  audioBuffer.push(new Uint8Array(pcmData));

  // Start timer if not already running
  if (!bufferTimer) {
    bufferTimer = setInterval(sendBufferedAudio, 200); // 0.2 seconds
  }
}

// Send buffered audio data every 0.2 seconds
function sendBufferedAudio() {
  if (audioBuffer.length === 0) {
    return;
  }

  // Calculate total length
  let totalLength = 0;
  for (const chunk of audioBuffer) {
    totalLength += chunk.length;
  }

  // Combine all chunks into a single buffer
  const combinedBuffer = new Uint8Array(totalLength);
  let offset = 0;
  for (const chunk of audioBuffer) {
    combinedBuffer.set(chunk, offset);
    offset += chunk.length;
  }

  // Send the combined audio data
  sendMessage({
    mime_type: "audio/pcm",
    data: arrayBufferToBase64(combinedBuffer.buffer),
  });
  console.log("[CLIENT TO AGENT] sent %s bytes", combinedBuffer.byteLength);

  // Clear the buffer
  audioBuffer = [];
}

// Stop audio recording and cleanup
function stopAudioRecording() {
  if (bufferTimer) {
    clearInterval(bufferTimer);
    bufferTimer = null;
  }

  // Send any remaining buffered audio
  if (audioBuffer.length > 0) {
    sendBufferedAudio();
  }
}

// Encode an array buffer with Base64
function arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

// Tickets functionality
let ticketsData = [];

// Load tickets on page load
document.addEventListener("DOMContentLoaded", function () {
  loadTickets();

  // Add refresh button event listener
  const refreshBtn = document.getElementById("refreshTicketsBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", loadTickets);
  }
});

async function loadTickets() {
  const container = document.getElementById("ticketsContainer");
  if (!container) return;

  try {
    container.innerHTML =
      '<div class="loading-tickets">Loading tickets...</div>';

    const response = await fetch("/api/tickets");
    const data = await response.json();

    if (data.error) {
      showTicketsError(data.error);
      return;
    }

    ticketsData = data.complaints || [];
    renderTickets();
  } catch (error) {
    console.error("Error loading tickets:", error);
    showTicketsError("Failed to load tickets. Please try again.");
  }
}

function renderTickets() {
  const container = document.getElementById("ticketsContainer");
  if (!container) return;

  if (ticketsData.length === 0) {
    container.innerHTML = '<div class="no-tickets">No tickets found.</div>';
    return;
  }

  // Show only the 5 most recent tickets
  const recentTickets = ticketsData
    .sort((a, b) => new Date(b.created_date) - new Date(a.created_date))
    .slice(0, 5);

  const ticketsHTML = recentTickets
    .map((ticket) => createTicketItem(ticket))
    .join("");
  container.innerHTML = ticketsHTML;
}

function createTicketItem(ticket) {
  const statusClass = getTicketStatusClass(ticket.status, ticket.priority);
  const priorityClass = ticket.priority === "high" ? "high-priority" : "";
  const cardClass = `ticket-item ${statusClass} ${priorityClass}`;

  const createdDate = new Date(ticket.created_date).toLocaleDateString();
  const timelineText = ticket.timeline_days
    ? `${ticket.timeline_days} days`
    : "N/A";

  return `
    <div class="${cardClass}">
      <div class="ticket-header">
        <div class="ticket-id">#${ticket.complaint_id}</div>
        <div class="ticket-status ${getTicketStatusClass(
          ticket.status,
          ticket.priority
        )}">
          ${getTicketStatusText(ticket.status, ticket.priority)}
        </div>
      </div>
      
      <div class="ticket-customer">
        Customer ID: ${ticket.customer_id} | Opus ID: ${ticket.opus_id}
      </div>
      
      <div class="ticket-subject">${ticket.subject}</div>
      <div class="ticket-issue">${ticket.issue}</div>
      
      <div class="ticket-meta">
        <span>📅 ${createdDate}</span>
        <span>⏱️ ${timelineText}</span>
      </div>
    </div>
  `;
}

function getTicketStatusClass(status, priority) {
  if (priority === "high") return "status-high-priority";
  if (status === "active") return "status-active";
  if (status === "closed") return "status-closed";
  return "";
}

function getTicketStatusText(status, priority) {
  if (priority === "high") return "High Priority";
  if (status === "active") return "Active";
  if (status === "closed") return "Closed";
  return status;
}

function showTicketsError(message) {
  const container = document.getElementById("ticketsContainer");
  if (container) {
    container.innerHTML = `<div class="tickets-error">❌ ${message}</div>`;
  }
}

/**
 * SESSIONS WITH TOBY — Google Apps Script Automation
 * ====================================================
 * HARDCODED LIMITS (free Google account):
 *   - Gmail sends: 100/day
 *   - URL fetch: 20,000/day
 *   - Total trigger runtime: 90 min/day
 *   - Per-script execution: 6 min
 *   - Properties service: 500KB total
 *
 * STRATEGY:
 *   - GAS handles: data routing, logic, orchestration, Sheets, Calendar
 *   - Brevo handles: bulk email sending (300/day on free plan)
 *   - Formsubmit.co as backup form endpoint
 *   - GAS web app as primary form endpoint
 *
 * SHEET STRUCTURE (create a Google Sheet named "Sessions with Toby — CRM"):
 *   Tab 1: "Leads" — name, email, phone, source, pain_point, status, date_added, last_contact, followup_count, notes
 *   Tab 2: "Sessions" — name, email, date, time, type, status, payment, notes
 *   Tab 3: "Email_Log" — timestamp, recipient, template, status, error
 *   Tab 4: "Metrics" — date, new_leads, emails_sent, sessions_booked, revenue
 */

// ═══════════════════════════════════════════════════════════
// CONFIG — Edit these values once
// ═══════════════════════════════════════════════════════════
var CONFIG = {
  SHEET_NAME: 'Sessions with Toby — CRM',
  LEADS_TAB: 'Leads',
  SESSIONS_TAB: 'Sessions',
  EMAIL_LOG_TAB: 'Email_Log',
  METRICS_TAB: 'Metrics',
  BREVO_API_KEY: PropertiesService.getScriptProperties().getProperty('BREVO_API_KEY') || '',
  BREVO_SENDER_EMAIL: 'prosperolumotobi@gmail.com',
  BREVO_SENDER_NAME: 'Coach Toby',
  COACH_EMAIL: 'prosperolumotobi@gmail.com',
  COACH_WHATSAPP: '2349160106084',
  MAX_EMAILS_PER_DAY: 90,        // Gmail fallback ceiling (stay under 100/day)
  MAX_BREVO_EMAILS_PER_DAY: 280, // Brevo primary ceiling (stay under 300/day, 20 buffer)
  TOTAL_DAILY_EMAIL_CEILING: 370, // Combined: Brevo 280 + Gmail 90
  TIMEZONE: 'Africa/Lagos',
  CALENDAR_ID: 'primary',
  FOLLOWUP_SEQUENCE_DELAYS: [0, 1, 3, 7, 14, 21], // Days after lead capture
  LEAD_SOURCES: ['quiz', 'vocal_pain', 'schedule', 'book', 'lead_magnet', 'community', 'direct']
};

// ═══════════════════════════════════════════════════════════
// WEB APP ENTRY POINT — Deploy as web app, receive form POSTs
// ═══════════════════════════════════════════════════════════
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var action = data.action || 'lead_capture';
    
    var result;
    switch(action) {
      case 'lead_capture':
        result = handleLeadCapture(data);
        break;
      case 'session_booking':
        result = handleSessionBooking(data);
        break;
      case 'brevo_webhook':
        result = handleBrevoWebhook(data);
        break;
      default:
        result = {success: false, error: 'Unknown action: ' + action};
    }
    
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch(err) {
    logError('doPost', err);
    return ContentService.createTextOutput(JSON.stringify({success: false, error: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  // Health check / manual trigger via GET
  var action = e.parameter.action || 'health';
  
  if (action === 'health') {
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      status: 'GAS web app is running',
      timestamp: new Date().toISOString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
  
  if (action === 'run_followup') {
    var result = runFollowUpSequence();
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  if (action === 'daily_digest') {
    var result = sendDailyDigest();
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  return ContentService.createTextOutput(JSON.stringify({success: false, error: 'Unknown action'}))
    .setMimeType(ContentService.MimeType.JSON);
}

// ═══════════════════════════════════════════════════════════
// LEAD CAPTURE — Receive form data, write to Sheet, trigger welcome email
// ═══════════════════════════════════════════════════════════
function handleLeadCapture(data) {
  var ss = getSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.LEADS_TAB);
  
  if (!sheet) {
    initializeSheets();
    sheet = ss.getSheetByName(CONFIG.LEADS_TAB);
  }
  
  // Check for duplicate email
  var email = (data.email || '').toLowerCase().trim();
  if (email) {
    var existing = findLeadByEmail(email);
    if (existing) {
      // Update existing lead
      return updateExistingLead(existing.row, data);
    }
  }
  
  // Add new lead
  var now = new Date();
  var row = [
    data.name || '',
    email,
    data.phone || '',
    data.source || 'direct',
    data.pain_point || '',
    'new',           // status
    now,             // date_added
    '',              // last_contact
    0,               // followup_count
    data.notes || ''
  ];
  
  sheet.appendRow(row);
  
  // Send welcome email immediately (count: 1)
  if (email) {
    sendWelcomeEmail(data.name || 'there', email);
  }
  
  // Notify coach of new lead
  notifyCoach('New Lead: ' + (data.name || email), 
    'Source: ' + (data.source || 'direct') + '\nPain: ' + (data.pain_point || 'N/A'));
  
  return {success: true, message: 'Lead captured', row: sheet.getLastRow()};
}

function updateExistingLead(row, data) {
  var ss = getSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.LEADS_TAB);
  
  // Update pain point if new one provided
  if (data.pain_point) {
    sheet.getRange(row, 5).setValue(data.pain_point);
  }
  // Update source to most recent
  if (data.source) {
    sheet.getRange(row, 4).setValue(data.source);
  }
  // Update notes
  if (data.notes) {
    var existingNotes = sheet.getRange(row, 10).getValue() || '';
    sheet.getRange(row, 10).setValue(existingNotes + '\n' + new Date().toLocaleDateString() + ': ' + data.notes);
  }
  // Set status to re-engaged
  sheet.getRange(row, 6).setValue('re-engaged');
  
  return {success: true, message: 'Lead updated', row: row};
}

// ═══════════════════════════════════════════════════════════
// SESSION BOOKING — Create calendar event + confirmation
// ═══════════════════════════════════════════════════════════
function handleSessionBooking(data) {
  var ss = getSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.SESSIONS_TAB);
  
  if (!sheet) {
    initializeSheets();
    sheet = ss.getSheetByName(CONFIG.SESSIONS_TAB);
  }
  
  var email = (data.email || '').toLowerCase().trim();
  var name = data.name || '';
  var date = data.session_date || '';
  var time = data.session_time || '';
  var type = data.session_type || '1-on-1';
  
  // Parse date/time
  var startDateTime = parseDateTime(date, time);
  if (!startDateTime) {
    return {success: false, error: 'Invalid date/time format'};
  }
  
  var endDateTime = new Date(startDateTime.getTime() + 60 * 60 * 1000); // 1 hour session
  
  // Create calendar event
  var calendar = CalendarApp.getCalendarById(CONFIG.CALENDAR_ID);
  var event;
  try {
    event = calendar.createEvent(
      'Session: ' + name,
      startDateTime,
      endDateTime,
      {
        description: 'Type: ' + type + '\nEmail: ' + email + '\nPhone: ' + (data.phone || 'N/A'),
        guests: email,
        sendInvites: true
      }
    );
  } catch(calErr) {
    logError('createCalendarEvent', calErr);
    // Continue — still log the booking even if calendar fails
  }
  
  // Write to Sessions sheet
  var row = [
    name,
    email,
    data.phone || '',
    date,
    time,
    type,
    'confirmed',     // status
    data.payment || 'pending',
    event ? event.getId() : '',
    new Date(),      // booked_at
    data.notes || ''
  ];
  sheet.appendRow(row);
  
  // Update lead status
  if (email) {
    var lead = findLeadByEmail(email);
    if (lead) {
      var leadsSheet = ss.getSheetByName(CONFIG.LEADS_TAB);
      leadsSheet.getRange(lead.row, 6).setValue('booked');
      leadsSheet.getRange(lead.row, 8).setValue(new Date());
    }
  }
  
  // Send confirmation email
  sendSessionConfirmation(name, email, date, time, type);
  
  // Notify coach
  notifyCoach('Session Booked: ' + name,
    date + ' at ' + time + '\nType: ' + type + '\nEmail: ' + email);
  
  return {success: true, message: 'Session booked', eventId: event ? event.getId() : null};
}

// ═══════════════════════════════════════════════════════════
// EMAIL FOLLOW-UP SEQUENCE — Time-triggered, runs daily
// ═══════════════════════════════════════════════════════════
function runFollowUpSequence() {
  var ss = getSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.LEADS_TAB);
  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  
  var today = new Date();
  today.setHours(0, 0, 0, 0);
  
  var emailsSent = 0;
  var errors = [];
  
  // Check daily email count (Brevo + Gmail combined)
  var dailyCount = getDailyEmailCount() + getDailyBrevoCount();
  if (dailyCount >= CONFIG.TOTAL_DAILY_EMAIL_CEILING) {
    return {success: false, error: 'Combined daily limit reached: ' + dailyCount + '/' + CONFIG.TOTAL_DAILY_EMAIL_CEILING};
  }
  
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var name = row[0];
    var email = row[1];
    var status = row[5];
    var dateAdded = row[6];
    var lastContact = row[7];
    var followupCount = row[8] || 0;
    
    // Skip if no email, already booked, or unsubscribed
    if (!email || status === 'booked' || status === 'unsubscribed' || status === 'converted') continue;
    
    // Calculate days since added
    var daysSince = Math.floor((today - new Date(dateAdded)) / (1000 * 60 * 60 * 24));
    
    // Check if it's time for next follow-up
    var nextFollowupDay = CONFIG.FOLLOWUP_SEQUENCE_DELAYS[followupCount];
    if (nextFollowupDay === undefined) continue; // Sequence complete
    
    if (daysSince >= nextFollowupDay) {
      // Check if already contacted today
      if (lastContact) {
        var lastContactDate = new Date(lastContact);
        lastContactDate.setHours(0, 0, 0, 0);
        if (lastContactDate.getTime() === today.getTime()) continue;
      }
      
      // Check limit before sending
      if (emailsSent >= (CONFIG.MAX_EMAILS_PER_DAY - dailyCount)) {
        errors.push('Limit reached after ' + emailsSent + ' emails');
        break;
      }
      
      // Send follow-up
      var sent = sendFollowUpEmail(name, email, followupCount);
      if (sent) {
        emailsSent++;
        // Update sheet
        sheet.getRange(i + 1, 8).setValue(new Date());  // last_contact
        sheet.getRange(i + 1, 9).setValue(followupCount + 1); // followup_count
        sheet.getRange(i + 1, 6).setValue('nurturing'); // status
      } else {
        errors.push('Failed: ' + email);
      }
      
      // Small delay to avoid rate limiting
      Utilities.sleep(1000);
    }
  }
  
  // Log metrics
  logMetric('followup_run', {emails_sent: emailsSent, errors: errors.length});
  
  return {success: true, emails_sent: emailsSent, errors: errors};
}

// ═══════════════════════════════════════════════════════════
// EMAIL TEMPLATES — All emails use anticipation architecture
// ═══════════════════════════════════════════════════════════
function sendWelcomeEmail(name, email) {
  var subject = 'Your voice is trying to tell you something';
  var body = [
    'Hi ' + name + ',',
    '',
    'You just took the first step most people never take.',
    '',
    'Not buying a course. Not watching another YouTube tutorial.',
    'Actually asking: "What\'s wrong with my voice — and how do I fix it?"',
    '',
    'That question changes everything.',
    '',
    'Here\'s what happens next:',
    '',
    '1. I\'ll send you a short breakdown of the #1 technique mistake I see in 80% of singers',
    '2. If it sounds like you, reply to this email — I read every single one',
    '3. If you want to skip the line, book a Vocal Breakthrough Session directly:',
    '   https://coachteesos.github.io/coachtoby-site/book.html',
    '',
    'Talk soon,',
    'Coach Toby',
    'Sessions with Toby',
    '',
    'P.S. — Your first session is guaranteed. If you don\'t hear a measurable difference, you don\'t pay.'
  ].join('\n');
  
  return sendEmail(email, subject, body, 'welcome');
}

function sendFollowUpEmail(name, email, followupCount) {
  var templates = [
    {
      subject: 'The mistake 80% of singers make (it\'s not what you think)',
      body: [
        'Hi ' + name + ',',
        '',
        'Quick question: When you sing, where do you feel the most tension?',
        '',
        'Throat? Jaw? Chest?',
        '',
        'Here\'s what most people get wrong:',
        '',
        'The tension you feel isn\'t the problem. It\'s the SYMPTOM.',
        '',
        'The real problem is what\'s happening 2 seconds BEFORE the tension hits.',
        'A breath that came from the wrong place. A note that was approached with the wrong intention.',
        '',
        'Fix the approach, and the tension disappears on its own.',
        '',
        'That\'s the entire philosophy behind Sessions with Toby.',
        '',
        'Want me to show you exactly where your approach is breaking down?',
        '→ https://coachteesos.github.io/coachtoby-site/book.html',
        '',
        'Coach Toby'
      ].join('\n')
    },
    {
      subject: 'What happened to [student name] in 3 weeks',
      body: [
        'Hi ' + name + ',',
        '',
        'A student came to me 3 weeks ago.',
        '',
        'She\'d been singing in her church choir for 6 years.',
        'Every single Sunday — throat tightens, voice cracks on the high note, sits down embarrassed.',
        '',
        'She thought she just wasn\'t "built" for singing.',
        '',
        'Session 1: We found the problem. It wasn\'t her voice. It was her breath approach.',
        'Session 2: We rebuilt her support from the ground up.',
        'Session 3: She sang the solo. No tightening. No cracking.',
        '',
        'She cried afterward.',
        '',
        'Same voice. Different understanding.',
        '',
        'If that sounds like something you need, the next step is simple:',
        '→ https://coachteesos.github.io/coachtoby-site/book.html',
        '',
        'Coach Toby'
      ].join('\n')
    },
    {
      subject: 'The gap between where you are and where you should be',
      body: [
        'Hi ' + name + ',',
        '',
        'There\'s a version of you that already knows how to sing the way you want to.',
        '',
        'That version exists. The voice is there. The range is there.',
        '',
        'The only thing standing between you and that version is:',
        '→ Understanding what your voice is actually doing under pressure',
        '→ One specific mechanical shift that changes everything',
        '',
        'That\'s it. Not 6 months of practice. Not another course.',
        'One shift. One session. One breakthrough.',
        '',
        'I\'ve seen it happen 50+ times now.',
        '',
        'Ready?',
        '→ https://coachteesos.github.io/coachtoby-site/book.html',
        '',
        'Coach Toby',
        '',
        'P.S. — Session 1 guarantee still stands. You hear a difference or you don\'t pay.'
      ].join('\n')
    },
    {
      subject: 'Last email — then I leave you alone',
      body: [
        'Hi ' + name + ',',
        '',
        'This is my last email in this sequence.',
        '',
        'Not because I don\'t want to help. But because I respect your inbox.',
        '',
        'If you\'re still reading this, part of you knows something needs to change.',
        '',
        'Here\'s the truth: Your voice is not the problem.',
        'The approach is the problem.',
        'And the approach can be fixed — usually in one session.',
        '',
        'If you\'re ready:',
        '→ https://coachteesos.github.io/coachtoby-site/book.html',
        '',
        'If not, no hard feelings. You know where to find me.',
        '',
        'Either way — keep singing.',
        '',
        'Coach Toby',
        'Sessions with Toby'
      ].join('\n')
    }
  ];
  
  var template = templates[Math.min(followupCount, templates.length - 1)];
  return sendEmail(email, template.subject, template.body, 'followup_' + followupCount);
}

function sendSessionConfirmation(name, email, date, time, type) {
  var subject = 'Session confirmed — here\'s what to expect';
  var body = [
    'Hi ' + name + ',',
    '',
    'Your ' + type + ' session is confirmed for:',
    date + ' at ' + time + ' (WAT)',
    '',
    'Here\'s what to do before we start:',
    '',
    '1. Find a quiet room with good internet',
    '2. Have a glass of water nearby (room temperature, not cold)',
    '3. Think about one specific thing you want to fix — we\'ll tackle it first',
    '',
    'The session link will be sent 30 minutes before we start.',
    '',
    'If you need to reschedule, just reply to this email or WhatsApp:',
    'https://wa.me/' + CONFIG.COACH_WHATSAPP,
    '',
    'See you on the call,',
    'Coach Toby'
  ].join('\n');
  
  return sendEmail(email, subject, body, 'session_confirmation');
}

// ═══════════════════════════════════════════════════════════
// BREVO WEBHOOK HANDLER — Track email engagement
// ═══════════════════════════════════════════════════════════
function handleBrevoWebhook(data) {
  var ss = getSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.LEADS_TAB);
  
  var event = data.event || '';
  var email = (data.email || '').toLowerCase().trim();
  
  if (!email) return {success: false, error: 'No email in webhook'};
  
  var lead = findLeadByEmail(email);
  if (!lead) return {success: true, message: 'Email not in CRM (ignored)'};
  
  var leadsSheet = ss.getSheetByName(CONFIG.LEADS_TAB);
  
  switch(event) {
    case 'opened':
      leadsSheet.getRange(lead.row, 10).setValue(
        (leadsSheet.getRange(lead.row, 10).getValue() || '') + '\nOpened: ' + new Date().toLocaleDateString()
      );
      break;
    case 'clicked':
      leadsSheet.getRange(lead.row, 6).setValue('engaged');
      leadsSheet.getRange(lead.row, 10).setValue(
        (leadsSheet.getRange(lead.row, 10).getValue() || '') + '\nClicked: ' + new Date().toLocaleDateString()
      );
      break;
    case 'unsubscribed':
      leadsSheet.getRange(lead.row, 6).setValue('unsubscribed');
      break;
    case 'bounced':
      leadsSheet.getRange(lead.row, 6).setValue('bounced');
      break;
  }
  
  return {success: true, event: event, email: email};
}

// ═══════════════════════════════════════════════════════════
// DAILY DIGEST — Send coach a summary every morning
// ═══════════════════════════════════════════════════════════
function sendDailyDigest() {
  var ss = getSpreadsheet();
  var leadsSheet = ss.getSheetByName(CONFIG.LEADS_TAB);
  var sessionsSheet = ss.getSheetByName(CONFIG.SESSIONS_TAB);
  var leads = leadsSheet.getDataRange().getValues();
  var sessions = sessionsSheet.getDataRange().getValues();
  
  var today = new Date();
  today.setHours(0, 0, 0, 0);
  
  var newLeads = 0;
  var engagedLeads = 0;
  var bookedToday = 0;
  var pendingFollowups = 0;
  
  for (var i = 1; i < leads.length; i++) {
    var leadDate = new Date(leads[i][6]);
    leadDate.setHours(0, 0, 0, 0);
    if (leadDate.getTime() === today.getTime()) newLeads++;
    if (leads[i][5] === 'engaged') engagedLeads++;
    
    var followupCount = leads[i][8] || 0;
    var daysSince = Math.floor((today - new Date(leads[i][6])) / (1000 * 60 * 60 * 24));
    var nextDay = CONFIG.FOLLOWUP_SEQUENCE_DELAYS[followupCount];
    if (nextDay !== undefined && daysSince >= nextDay) pendingFollowups++;
  }
  
  for (var j = 1; j < sessions.length; j++) {
    var sessionDate = new Date(sessions[j][3]);
    sessionDate.setHours(0, 0, 0, 0);
    if (sessionDate.getTime() === today.getTime()) bookedToday++;
  }
  
  var subject = 'Daily Digest — ' + Utilities.formatDate(today, CONFIG.TIMEZONE, 'MMM dd, yyyy');
  var body = [
    'Good morning Coach Toby,',
    '',
    'Here\'s your daily snapshot:',
    '',
    '📊 LEADS',
    '   New today: ' + newLeads,
    '   Total engaged: ' + engagedLeads,
    '   Pending follow-ups: ' + pendingFollowups,
    '',
    '📅 SESSIONS',
    '   Booked today: ' + bookedToday,
    '',
    '📧 EMAILS',
    '   Sent today: ' + getDailyEmailCount() + '/' + CONFIG.MAX_EMAILS_PER_DAY,
    '',
    'CRM: https://docs.google.com/spreadsheets/d/' + ss.getId(),
    '',
    '— Sessions with Toby Automation'
  ].join('\n');
  
  sendEmail(CONFIG.COACH_EMAIL, subject, body, 'daily_digest');
  
  return {success: true, new_leads: newLeads, engaged: engagedLeads, pending: pendingFollowups};
}

// ═══════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════
function getSpreadsheet() {
  var props = PropertiesService.getScriptProperties();
  var sheetId = props.getProperty('SHEET_ID');
  
  if (sheetId) {
    return SpreadsheetApp.openById(sheetId);
  }
  
  // Try to find by name
  var files = DriveApp.getFilesByName(CONFIG.SHEET_NAME);
  if (files.hasNext()) {
    var file = files.next();
    props.setProperty('SHEET_ID', file.getId());
    return SpreadsheetApp.openById(file.getId());
  }
  
  throw new Error('Spreadsheet "' + CONFIG.SHEET_NAME + '" not found. Create it first, then set SHEET_ID in Script Properties.');
}

// ═══════════════════════════════════════════════════════════
// REPLY TRACKER — Polls Gmail for student replies, logs to Sheet
// Run every 15-30 min via time trigger
// ═══════════════════════════════════════════════════════════
function checkStudentReplies() {
  try {
    // Search for replies in threads we initiated
    // Looks for emails FROM student addresses IN threads we sent to
    var ss = getSpreadsheet();
    var leadsSheet = ss.getSheetByName(CONFIG.LEADS_TAB);
    var leadsData = leadsSheet.getDataRange().getValues();
    
    // Build list of student emails
    var studentEmails = [];
    for (var i = 1; i < leadsData.length; i++) {
      if (leadsData[i][1]) studentEmails.push(leadsData[i][1].toLowerCase().trim());
    }
    
    if (studentEmails.length === 0) return {success: true, checked: 0, new_replies: 0};
    
    // Get last check timestamp from script properties
    var props = PropertiesService.getScriptProperties();
    var lastCheck = props.getProperty('last_reply_check');
    
    // Build targeted search query using last check timestamp
    // Format: after:YYYY/MM/DD for Gmail search
    var lastCheckDate = lastCheck ? new Date(lastCheck) : new Date(Date.now() - 24 * 60 * 60 * 1000);
    var afterStr = Utilities.formatDate(lastCheckDate, 'GMT', 'yyyy/MM/dd');
    
    // Tight query: only threads we sent, with messages AFTER last check, NOT from us
    // This means: threads where someone replied since we last checked
    var searchQuery = 'in:sent -from:' + CONFIG.COACH_EMAIL + ' after:' + afterStr;
    
    var threads = GmailApp.search(searchQuery, 0, 50);
    
    // Early exit if no threads with new replies
    if (threads.length === 0) {
      props.setProperty('last_reply_check', new Date().toISOString());
      return {success: true, checked: 0, new_replies: 0};
    }
    
    var newReplies = 0;
    var replyLog = ss.getSheetByName('Reply_Log');
    if (!replyLog) {
      replyLog = ss.insertSheet('Reply_Log');
      replyLog.appendRow(['Date', 'Student Email', 'Subject', 'Snippet', 'Thread ID']);
      replyLog.getRange(1, 1, 1, 5).setFontWeight('bold');
      replyLog.setFrozenRows(1);
    }
    
    for (var t = 0; t < threads.length; t++) {
      var thread = threads[t];
      var messages = thread.getMessages();
      
      for (var m = 0; m < messages.length; m++) {
        var msg = messages[m];
        var from = msg.getFrom().toLowerCase();
        var msgDate = msg.getDate();
        
        // Skip if from coach, or before last check
        if (from.indexOf(CONFIG.COACH_EMAIL.toLowerCase()) !== -1) continue;
        if (msgDate <= lastCheckDate) continue;
        
        // Check if sender is a known lead
        var isLead = false;
        for (var s = 0; s < studentEmails.length; s++) {
          if (from.indexOf(studentEmails[s]) !== -1) {
            isLead = true;
            break;
          }
        }
        
        if (isLead) {
          replyLog.appendRow([
            msgDate,
            from,
            msg.getSubject(),
            msg.getPlainBody().substring(0, 200).replace(/\n/g, ' '),
            thread.getId()
          ]);
          newReplies++;
          
          // Update lead status
          var lead = findLeadByEmail(from.replace(/.*<(.+)>.*/, '$1').trim());
          if (lead) {
            leadsSheet.getRange(lead.row, 6).setValue('replied');
            leadsSheet.getRange(lead.row, 8).setValue(new Date());
            var notes = leadsSheet.getRange(lead.row, 10).getValue() || '';
            leadsSheet.getRange(lead.row, 10).setValue(
              notes + '\n[REPLY ' + Utilities.formatDate(msgDate, CONFIG.TIMEZONE, 'MMM dd HH:mm') + ']: ' + 
              msg.getPlainBody().substring(0, 100).replace(/\n/g, ' ')
            );
          }
        }
      }
    }
    
    // Update last check timestamp
    props.setProperty('last_reply_check', new Date().toISOString());
    
    return {success: true, checked: threads.length, new_replies: newReplies};
    
  } catch(err) {
    logError('checkStudentReplies', err);
    return {success: false, error: err.toString()};
  }
}

function findLeadByEmail(email) {
  var ss = getSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.LEADS_TAB);
  var data = sheet.getDataRange().getValues();
  
  for (var i = 1; i < data.length; i++) {
    if ((data[i][1] || '').toLowerCase().trim() === email.toLowerCase().trim()) {
      return {row: i + 1, data: data[i]};
    }
  }
  return null;
}

function sendEmail(to, subject, body, templateName) {
  // PRIMARY: Brevo API (300/day free)
  var brevoSent = sendViaBrevo(to, subject, body);
  
  if (brevoSent) {
    logEmail(to, templateName, 'sent_brevo', '');
    return true;
  }
  
  // FALLBACK: GmailApp (100/day free) — for coach notifications
  try {
    GmailApp.sendEmail(to, subject, body, {
      name: CONFIG.BREVO_SENDER_NAME,
      replyTo: CONFIG.COACH_EMAIL
    });
    logEmail(to, templateName, 'sent_gmail', '');
    return true;
  } catch(err) {
    logEmail(to, templateName, 'failed', err.toString().substring(0, 200));
    return false;
  }
}

function sendViaBrevo(to, subject, body) {
  if (!CONFIG.BREVO_API_KEY) return false;
  
  // Check Brevo daily count
  var brevoCount = getDailyBrevoCount();
  if (brevoCount >= CONFIG.MAX_BREVO_EMAILS_PER_DAY) return false;
  
  try {
    var payload = {
      sender: { email: CONFIG.BREVO_SENDER_EMAIL, name: CONFIG.BREVO_SENDER_NAME },
      to: [{ email: to }],
      subject: subject,
      textContent: body
    };
    
    var response = UrlFetchApp.fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'post',
      contentType: 'application/json',
      headers: { 'api-key': CONFIG.BREVO_API_KEY },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
    
    var code = response.getResponseCode();
    if (code >= 200 && code < 300) {
      incrementBrevoCount();
      return true;
    }
    return false;
  } catch(err) {
    return false;
  }
}

function getDailyBrevoCount() {
  try {
    var cache = CacheService.getScriptCache();
    var count = cache.get('brevo_count_' + Utilities.formatDate(new Date(), CONFIG.TIMEZONE, 'yyyy-MM-dd'));
    return count ? parseInt(count) : 0;
  } catch(e) { return 0; }
}

function incrementBrevoCount() {
  try {
    var cache = CacheService.getScriptCache();
    var key = 'brevo_count_' + Utilities.formatDate(new Date(), CONFIG.TIMEZONE, 'yyyy-MM-dd');
    var count = getDailyBrevoCount() + 1;
    cache.put(key, count.toString(), 86400); // 24hr TTL
  } catch(e) {}
}

function logEmail(to, template, status, error) {
  try {
    var ss = getSpreadsheet();
    var logSheet = ss.getSheetByName(CONFIG.EMAIL_LOG_TAB);
    if (logSheet) {
      logSheet.appendRow([new Date(), to, template, status, error || '']);
    }
  } catch(e) {}
}

function notifyCoach(subject, body) {
  return sendEmail(CONFIG.COACH_EMAIL, '[SWT] ' + subject, body, 'coach_notification');
}

function parseDateTime(dateStr, timeStr) {
  try {
    // Expected format: date = "2026-06-15", time = "14:00"
    var parts = dateStr.split('-');
    var timeParts = timeStr.split(':');
    return new Date(
      parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]),
      parseInt(timeParts[0]), parseInt(timeParts[1] || 0)
    );
  } catch(e) {
    return null;
  }
}

function getDailyEmailCount() {
  var ss = getSpreadsheet();
  var logSheet = ss.getSheetByName(CONFIG.EMAIL_LOG_TAB);
  if (!logSheet) return 0;
  
  var data = logSheet.getDataRange().getValues();
  var today = new Date();
  today.setHours(0, 0, 0, 0);
  var count = 0;
  
  for (var i = 1; i < data.length; i++) {
    var logDate = new Date(data[i][0]);
    logDate.setHours(0, 0, 0, 0);
    if (logDate.getTime() === today.getTime() && data[i][3] === 'sent') {
      count++;
    }
  }
  return count;
}

function logError(context, error) {
  try {
    console.error('[' + context + '] ' + error.toString());
    var ss = getSpreadsheet();
    var logSheet = ss.getSheetByName(CONFIG.EMAIL_LOG_TAB);
    if (logSheet) {
      logSheet.appendRow([new Date(), '', 'ERROR:' + context, 'error', error.toString().substring(0, 500)]);
    }
  } catch(e) {
    // Last resort — just console
    console.error('Log failed: ' + e.toString());
  }
}

function logMetric(type, data) {
  try {
    var ss = getSpreadsheet();
    var sheet = ss.getSheetByName(CONFIG.METRICS_TAB);
    if (sheet) {
      sheet.appendRow([new Date(), type, JSON.stringify(data)]);
    }
  } catch(e) {
    // Non-critical
  }
}

// ═══════════════════════════════════════════════════════════
// SHEET INITIALIZATION — Run once to set up tabs
// ═══════════════════════════════════════════════════════════
function initializeSheets() {
  var ss = getSpreadsheet();
  
  // Leads tab
  var leads = ss.getSheetByName(CONFIG.LEADS_TAB);
  if (!leads) {
    leads = ss.insertSheet(CONFIG.LEADS_TAB);
    leads.appendRow(['Name', 'Email', 'Phone', 'Source', 'Pain Point', 'Status', 'Date Added', 'Last Contact', 'Follow-up Count', 'Notes']);
    leads.getRange(1, 1, 1, 10).setFontWeight('bold');
    leads.setFrozenRows(1);
  }
  
  // Sessions tab
  var sessions = ss.getSheetByName(CONFIG.SESSIONS_TAB);
  if (!sessions) {
    sessions = ss.insertSheet(CONFIG.SESSIONS_TAB);
    sessions.appendRow(['Name', 'Email', 'Phone', 'Date', 'Time', 'Type', 'Status', 'Payment', 'Calendar Event ID', 'Booked At', 'Notes']);
    sessions.getRange(1, 1, 1, 11).setFontWeight('bold');
    sessions.setFrozenRows(1);
  }
  
  // Email Log tab
  var emailLog = ss.getSheetByName(CONFIG.EMAIL_LOG_TAB);
  if (!emailLog) {
    emailLog = ss.insertSheet(CONFIG.EMAIL_LOG_TAB);
    emailLog.appendRow(['Timestamp', 'Recipient', 'Template', 'Status', 'Error']);
    emailLog.getRange(1, 1, 1, 5).setFontWeight('bold');
    emailLog.setFrozenRows(1);
  }
  
  // Metrics tab
  var metrics = ss.getSheetByName(CONFIG.METRICS_TAB);
  if (!metrics) {
    metrics = ss.insertSheet(CONFIG.METRICS_TAB);
    metrics.appendRow(['Timestamp', 'Type', 'Data']);
    metrics.getRange(1, 1, 1, 3).setFontWeight('bold');
    metrics.setFrozenRows(1);
  }
  
  return {success: true, message: 'Sheets initialized'};
}

// ═══════════════════════════════════════════════════════════
// TRIGGER SETUP — Run once to create time triggers
// ═══════════════════════════════════════════════════════════
function setupTriggers() {
  // Delete existing triggers first
  var triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(t) { ScriptApp.deleteTrigger(t); });
  
  // Daily follow-up sequence at 10:00 AM WAT
  ScriptApp.newTrigger('runFollowUpSequence')
    .timeBased()
    .atHour(10)
    .nearMinute(0)
    .everyDays(1)
    .create();
  
  // Daily digest at 8:00 AM WAT
  ScriptApp.newTrigger('sendDailyDigest')
    .timeBased()
    .atHour(8)
    .nearMinute(0)
    .everyDays(1)
    .create();
  
  // Reply checker every 30 minutes
  ScriptApp.newTrigger('checkStudentReplies')
    .timeBased()
    .everyMinutes(30)
    .create();
  
  return {success: true, message: 'Triggers set: follow-up 10AM, digest 8AM, reply check every 30min (WAT)'};
}

// ═══════════════════════════════════════════════════════════
// MANUAL TEST — Run to verify everything works
// ═══════════════════════════════════════════════════════════
function testLeadCapture() {
  var result = handleLeadCapture({
    name: 'Test User',
    email: 'test@example.com',
    phone: '+2340000000000',
    source: 'test',
    pain_point: 'throat tightens on high notes',
    notes: 'Manual test lead'
  });
  Logger.log(JSON.stringify(result));
  return result;
}

function testFollowUp() {
  var result = runFollowUpSequence();
  Logger.log(JSON.stringify(result));
  return result;
}

function testDigest() {
  var result = sendDailyDigest();
  Logger.log(JSON.stringify(result));
  return result;
}

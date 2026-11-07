/**
 * Reference content of unstructured communications (Teams, Email, SMS)
 * to allow inspection directly within the UI.
 */

export const RAW_TEAMS_THREADS = [
  {
    id: 'TH-T-001',
    topic: 'TRN-042 traffic stall after SFP replacement',
    participants: ['Erkki Expert', 'Veikko Vikkelä'],
    messages: [
      {
        author: 'Veikko Vikkelä',
        time: '2026-03-12T09:12:00+02:00',
        text: 'Replaced faulty SFP on TRN-042 (Nokia mast). Link is operationally UP and optical RX is -5.2 dBm (nominal), alarms cleared. But traffic counters remain strictly at zero! Should I reboot or replace with another spare?',
      },
      {
        author: 'Erkki Expert',
        time: '2026-03-12T09:21:00+02:00',
        text: 'Do NOT reboot and do not swap the SFP again! Known hardware quirk on older TX-2000 units (~2019 batch). The internal forwarding pipeline fails to re-initialize after an optics hot-swap.',
      },
      {
        author: 'Erkki Expert',
        time: '2026-03-12T09:22:00+02:00',
        text: 'Workaround: execute administrative disable on the interface, wait ~30 seconds, then re-enable. Traffic counters will resume immediately.',
      },
      {
        author: 'Veikko Vikkelä',
        time: '2026-03-12T09:25:00+02:00',
        text: 'Worked like a charm! Flapped the port and packets started flowing immediately. Saved me a 2-hour chassis reboot cycle.',
      },
    ],
  },
  {
    id: 'TH-T-002',
    topic: 'TRN-021 CRC errors after storm (Disputed Guidance)',
    participants: ['Aino Asiantuntija', 'Mikko Mäkelä', 'Veikko Vikkelä'],
    messages: [
      {
        author: 'Veikko Vikkelä',
        time: '2026-07-18T14:32:00+03:00',
        text: 'TRN-021 port 1/1/3 CRC errors climbing rapidly since the thunderstorm. Link UP, optics normal (-6 dBm). What should I inspect first?',
      },
      {
        author: 'Aino Asiantuntija',
        time: '2026-07-18T14:35:00+03:00',
        text: 'Always clean connectors first on TX-3000! After storms we regularly see particulate contamination at Hervanta. Clean and inspect both patch ends before touching the line card.',
      },
      {
        author: 'Mikko Mäkelä',
        time: '2026-07-18T14:38:00+03:00',
        text: 'I disagree. On TX-3000 the line card gets into a corrupted state after voltage sags. Reseating the line card resolved TRN-001 in May.',
      },
      {
        author: 'Aino Asiantuntija',
        time: '2026-07-18T14:40:00+03:00',
        text: 'Reseating takes down all ports on the card and drops live services! Clean connectors first—it is non-disruptive.',
      },
    ],
  },
  {
    id: 'TH-T-004',
    topic: 'TX-2000 firmware 4.2 upgrade status',
    participants: ['Aino Asiantuntija', 'Erkki Expert'],
    messages: [
      {
        author: 'Aino Asiantuntija',
        time: '2026-09-22T10:15:00+03:00',
        text: 'Firmware 4.2 has been rolled out to ~40% of the TX-2000 fleet. The optic hot-swap re-init bug is resolved in 4.2+.',
      },
      {
        author: 'Erkki Expert',
        time: '2026-09-22T10:20:00+03:00',
        text: 'Good to know. For units remaining on firmware < 4.2 (like TRN-117), the port flap workaround is still required.',
      },
    ],
  },
];

export const RAW_EMAILS = [
  {
    id: 'TH-E-003',
    subject: 'SAL-03 barrier key - new arrangement',
    from: 'pekka.pohjonen@operator.fi',
    date: '2026-05-20T11:05:00+03:00',
    body: 'The landowner has installed a combination keybox at the Hirvasvaarantie barrier (SAL-03). The key is NO LONGER kept at Sallan Kyläkauppa.\n\nThe keybox code is available from the NOC on request before dispatch. Please call the NOC before you leave for the site.',
    note: 'ACTIVE access assertion. Supersedes TH-E-002.',
  },
  {
    id: 'TH-E-002',
    subject: 'Hirvasvaara mast (SAL-03) - road now has a barrier',
    from: 'pekka.pohjonen@operator.fi',
    date: '2024-10-15T14:22:00+03:00',
    body: 'FYI the landowner has put a locked barrier at the start of Hirvasvaarantie (SAL-03 access road), 2.4 km before the mast.\n\nThe key is kept at Sallan Kyläkauppa in the village centre. Return the key the same day.\nIn winter the road is ploughed only up to the barrier; bring snowmobile from there.',
    note: 'HISTORICAL / SUPERSEDED by TH-E-003.',
  },
  {
    id: 'TH-E-001',
    subject: 'TX-2000 SFP swap workaround documented',
    from: 'erkki.expert@operator.fi',
    date: '2026-03-12T10:15:00+02:00',
    body: 'Summary of earlier TRN-042 incident: after SFP replacement, interface stays operationally UP but forwarding counters remain at zero.\n\nWorkaround: disable interface, wait 30 seconds, re-enable. No reboot needed.',
    note: 'Matches TRN-042 and TRN-117 symptoms.',
  },
];

export const RAW_SMS = [
  {
    id: 'TH-S-001',
    thread: 'Pekka Pohjola (Field Eng)',
    messages: [
      {
        time: '2026-01-14T09:50:00+02:00',
        sender: 'Pekka Pohjola',
        text: 'At SAL-03 road. Barrier is locked and I have no key. Anyone know where the key is?',
      },
      {
        time: '2026-01-14T11:35:00+02:00',
        sender: 'Pekka Pohjola',
        text: 'Found an old email from Oct 2024: key is at Sallan Kyläkauppa. Going to pick it up now. Lost 1h 45m waiting here.',
      },
    ],
  },
];

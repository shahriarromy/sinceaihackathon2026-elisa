import { useState } from 'react';
import {
  Card,
  Text,
  Title,
  Group,
  Badge,
  Button,
  Stack,
  Paper,
  Box,
  Collapse,
  Code,
} from '@mantine/core';
import {
  IconArrowRight,
  IconCode,
} from '@tabler/icons-react';

interface SequenceLane {
  id: string;
  code: string;
  title: string;
  element: string;
  model: string;
  site: string;
  date: string;
  status: 'RESOLVED' | 'ROUTINE' | 'OPEN';
  duration: string;
  isOpen?: boolean;
  steps: {
    time: string;
    label: string;
    type: 'fault' | 'analysis' | 'field' | 'access' | 'accessBlock' | 'state' | 'recovery' | 'pending';
    wait?: string;
  }[];
  knowledge: {
    id: string;
    type: 'known' | 'disputed' | 'missed';
    title: string;
    detail: string;
    source: string;
  };
}

const LANES: SequenceLane[] = [
  {
    id: 'W1',
    code: 'WO-2026-0114-002',
    title: 'Locked barrier on private road',
    element: 'TRN-233',
    model: 'TX-2000',
    site: 'SAL-03 Salla',
    date: '14 Jan 2026',
    status: 'RESOLVED',
    duration: '6 h 8 min',
    steps: [
      { time: '06:40', label: 'Device unreachable', type: 'fault' },
      { time: '06:55', label: 'AI RCA: PSU', type: 'analysis' },
      { time: '07:05', label: 'Dispatch', type: 'field' },
      { time: '09:50', label: 'Access blocked by barrier', type: 'accessBlock', wait: '1 h 45 min lost' },
      { time: '11:35', label: 'Access granted, key found', type: 'access' },
      { time: '12:40', label: 'PSU replaced', type: 'field' },
      { time: '12:48', label: 'Alarm cleared', type: 'recovery' },
    ],
    knowledge: {
      id: 'CA-0002',
      type: 'missed',
      title: 'EXISTED, NOT USED',
      detail: 'Key kept at Sallan Kyläkauppa village shop. Advice in Oct 2024 email was missed by field engineer, causing 1h 45m wasted outage time.',
      source: 'Pekka Pohjola, Email Oct 2024',
    },
  },
  {
    id: 'W2',
    code: 'WO-2026-0312-007',
    title: "Erkki's case — Forwarding stall after SFP swap",
    element: 'TRN-042',
    model: 'TX-2000',
    site: 'TRE-03 Nokia',
    date: '12 Mar 2026',
    status: 'RESOLVED',
    duration: '1 h 23 min',
    steps: [
      { time: '08:02', label: 'Loss of signal', type: 'fault' },
      { time: '08:10', label: 'Dispatch', type: 'field' },
      { time: '09:05', label: 'SFP replaced', type: 'field' },
      { time: '09:06', label: 'Alarm cleared, interface UP', type: 'state', wait: '19 min UP but no traffic' },
      { time: '09:23', label: 'Interface disabled', type: 'field' },
      { time: '09:24', label: 'Interface enabled', type: 'field' },
      { time: '09:25', label: 'Traffic restored', type: 'recovery' },
    ],
    knowledge: {
      id: 'CA-0001',
      type: 'known',
      title: 'CAPTURED HERE',
      detail: 'Disable and re-enable interface after SFP swap on older TX-2000 units. Do not reboot or replace hardware.',
      source: 'Erkki Expert, Teams thread TH-T-001 & Email TH-E-001',
    },
  },
  {
    id: 'W3',
    code: 'WO-2026-0718-011',
    title: 'Rising CRC errors after storm (Disputed Guidance)',
    element: 'TRN-021',
    model: 'TX-3000',
    site: 'TRE-01 Hervanta',
    date: '18-19 Jul 2026',
    status: 'RESOLVED',
    duration: '19 h 45 min',
    steps: [
      { time: '14:20', label: 'CRC errors', type: 'fault' },
      { time: '14:50', label: 'Connectors cleaned', type: 'field', wait: 'next day' },
      { time: '+1d 08:30', label: 'CRC errors again', type: 'fault' },
      { time: '+1d 09:55', label: 'Line card reseated', type: 'field' },
      { time: '+1d 10:05', label: 'Cleared', type: 'recovery' },
    ],
    knowledge: {
      id: 'CA-0004 & CA-0005',
      type: 'disputed',
      title: 'DISPUTED GUIDANCE',
      detail: 'Clean optical connectors first (Aino, non-disruptive) vs Reseat line card (Mikko, disruptive - drops all ports). Incident Investigator prioritizes non-disruptive cleaning first.',
      source: 'Teams thread TH-T-002',
    },
  },
  {
    id: 'W4',
    code: 'WO-2026-1003-004',
    title: 'Routine radio alignment check',
    element: 'MWR-233',
    model: 'MW-500',
    site: 'SAL-03 Salla',
    date: '3 Oct 2026',
    status: 'ROUTINE',
    duration: '4 h 50 min',
    steps: [
      { time: '09:05', label: 'Barrier opened with keybox code', type: 'access' },
    ],
    knowledge: {
      id: 'CA-0003',
      type: 'known',
      title: 'CONFIRMED BY THIS VISIT',
      detail: 'Keybox installed at Hirvasvaarantie barrier. Code obtained from NOC before departure. Supersedes CA-0002 (village shop key).',
      source: 'Sanna Saarinen, Email TH-E-003',
    },
  },
  {
    id: 'W5',
    code: 'WO-2026-1107-003',
    title: 'Traffic not restored after SFP swap (ONGOING OUTAGE)',
    element: 'TRN-117',
    model: 'TX-2000 fw 4.1',
    site: 'OUL-05 Kiiminki',
    date: '7 Nov 2026',
    status: 'OPEN',
    duration: 'Ongoing',
    isOpen: true,
    steps: [
      { time: '07:12', label: 'Loss of signal', type: 'fault' },
      { time: '07:20', label: 'Dispatch', type: 'field' },
      { time: '08:35', label: 'SFP replaced', type: 'field' },
      { time: '08:36', label: 'Alarm cleared, interface UP', type: 'state', wait: 'UP but no traffic (ongoing)' },
      { time: '08:45', label: 'Traffic still zero', type: 'pending' },
    ],
    knowledge: {
      id: 'CA-0009',
      type: 'known',
      title: 'MATCHES 4/4 SYMPTOMS',
      detail: 'TX-2000 below fw 4.2: interface UP, RX normal, alarms cleared, traffic zero. Disable interface, wait 30s, enable. Applying this captured knowledge resolves the outage immediately.',
      source: 'Erkki Expert & Aino Asiantuntija (learned on TRN-042)',
    },
  },
];

const RAW_MERMAID_SOURCE = `flowchart TB
  subgraph W1["WO-2026-0114-002 · Locked barrier · TRN-233 (TX-2000, SAL-03 Salla) · 14 Jan 2026 · RESOLVED · 6 h 8 min"]
    A1["06:40 Device unreachable"]:::fault --> A2["06:55 AI root cause: PSU"]:::analysis
    A2 --> A3["07:05 Dispatch"]:::field
    A3 --> A4["09:50 Access blocked by barrier"]:::accessBlock
    A4 -- "1 h 45 min lost" --> A5["11:35 Access granted, key found"]:::access
    A5 --> A6["12:40 PSU replaced"]:::field
    A6 --> A7["12:48 Alarm cleared"]:::recovery
    K1{{"CA-0002 · EXISTED, NOT USED"}}:::missed
    A4 -.- K1
  end

  subgraph W2["WO-2026-0312-007 · Erkki's case · TRN-042 (TX-2000, TRE-03 Nokia) · 12 Mar 2026 · RESOLVED · 1 h 23 min"]
    B1["08:02 Loss of signal"]:::fault --> B2["08:10 Dispatch"]:::field
    B2 --> B3["09:05 SFP replaced"]:::field
    B3 --> B4["09:06 Alarm cleared, interface UP"]:::state
    B4 -- "19 min UP but no traffic" --> B5["09:23 Interface disabled"]:::field
    B5 --> B6["09:24 Interface enabled"]:::field
    B6 --> B7["09:25 Traffic restored"]:::recovery
    K2{{"CA-0001 · CAPTURED HERE"}}:::known
    B5 -.- K2
  end

  subgraph W3["WO-2026-0718-011 · Conflicting advice · TRN-021 (TX-3000, TRE-01 Hervanta) · 18-19 Jul 2026 · RESOLVED · 19 h 45 min"]
    C1["14:20 CRC errors"]:::fault --> C2["14:50 Connectors cleaned"]:::field
    C2 -- "next day" --> C3["+1d 08:30 CRC errors again"]:::fault
    C3 --> C4["+1d 09:55 Line card reseated"]:::field
    C4 --> C5["+1d 10:05 Cleared"]:::recovery
    K3a{{"CA-0004 · DISPUTED"}}:::disputed
    K3b{{"CA-0005 · DISPUTED"}}:::disputed
    C2 -.- K3a
    C4 -.- K3b
  end

  subgraph W4["WO-2026-1003-004 · Routine visit · MWR-233 (MW-500, SAL-03 Salla) · 3 Oct 2026 · ROUTINE"]
    D1["09:05 Barrier opened with keybox code"]:::access
    K4{{"CA-0003 · CONFIRMED BY THIS VISIT"}}:::known
    D1 -.- K4
  end

  subgraph W5["WO-2026-1107-003 · Traffic not restored · TRN-117 (TX-2000 fw 4.1, OUL-05 Kiiminki) · 7 Nov 2026 · OPEN"]
    E1["07:12 Loss of signal"]:::fault --> E2["07:20 Dispatch"]:::field
    E2 --> E3["08:35 SFP replaced"]:::field
    E3 --> E4["08:36 Alarm cleared, interface UP"]:::state
    E4 -- "UP but no traffic (ongoing)" --> E5(["08:45 Traffic still zero"]):::pending
    K5{{"CA-0009 · MATCHES 4/4 SYMPTOMS"}}:::known
    E5 -.- K5
  end`;

export default function SequencesFlowView({ onSelectIncident }: { onSelectIncident?: (id: string) => void }) {
  const [showCode, setShowCode] = useState(false);

  const getStepBg = (type: string) => {
    switch (type) {
      case 'fault':
        return { bg: '#fbe7e4', border: '#c0392b', color: '#142029' };
      case 'analysis':
        return { bg: '#ece6fb', border: '#6a4bc4', color: '#142029' };
      case 'field':
        return { bg: '#e3f1f3', border: '#0a6c78', color: '#142029' };
      case 'access':
        return { bg: '#fbefdc', border: '#a8660b', color: '#142029' };
      case 'accessBlock':
        return { bg: '#fbefdc', border: '#a8660b', color: '#142029', bold: true };
      case 'state':
        return { bg: '#edf2f5', border: '#6b7b88', color: '#142029' };
      case 'recovery':
        return { bg: '#e2f3e9', border: '#2a7d4f', color: '#142029' };
      case 'pending':
        return { bg: '#fff7f6', border: '#c0392b', color: '#c0392b', dashed: true };
      default:
        return { bg: '#edf2f5', border: '#6b7b88', color: '#142029' };
    }
  };

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="flex-start">
        <div>
          <Title order={2} style={{ letterSpacing: -0.5 }}>
            Incident Sequences & Resolution Timelines
          </Title>
          <Text c="dimmed" size="sm">
            5 work orders from the Elisa × Since AI 2026 demo network, visualising how expert field advice is captured, validated, and applied.
          </Text>
        </div>

        <Button
          variant="outline"
          color="gray"
          size="xs"
          leftSection={<IconCode size={14} />}
          onClick={() => setShowCode(!showCode)}
        >
          {showCode ? 'Hide Mermaid Source' : 'View Mermaid Source'}
        </Button>
      </Group>

      {/* Mermaid Raw Code Collapse */}
      <Collapse in={showCode}>
        <Paper withBorder p="md" radius="md">
          <Group justify="space-between" mb="xs">
            <Text fw={600} size="sm">Mermaid Source (diagrams/incident-sequences.mmd)</Text>
            <Badge color="gray" size="xs">Flowchart TB</Badge>
          </Group>
          <Code block style={{ maxHeight: 250, overflowY: 'auto' }}>
            {RAW_MERMAID_SOURCE}
          </Code>
        </Paper>
      </Collapse>

      {/* Semantic Legend Bar */}
      <Card withBorder padding="xs" radius="md">
        <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={6}>
          Diagram Semantic Colors & Knowledge Legend
        </Text>
        <Group gap="xs" wrap="wrap">
          <Badge color="red" variant="light" size="xs">Fault (Loss of signal, CRC)</Badge>
          <Badge color="violet" variant="light" size="xs">Root Cause Analysis</Badge>
          <Badge color="blue" variant="light" size="xs">Field Action (SFP swap, Port flap)</Badge>
          <Badge color="orange" variant="light" size="xs">Site Access (Barrier key)</Badge>
          <Badge color="gray" variant="light" size="xs">Interface UP / State Change</Badge>
          <Badge color="green" variant="light" size="xs">Traffic Restored (Recovery)</Badge>
          <Badge color="red" variant="outline" size="xs">Pending / Unresolved State</Badge>
          <Badge color="green" variant="filled" size="xs">Hexagon: Captured Knowledge</Badge>
          <Badge color="orange" variant="filled" size="xs">Hexagon: Disputed Advice</Badge>
          <Badge color="red" variant="filled" size="xs">Hexagon: Missed Knowledge</Badge>
        </Group>
      </Card>

      {/* 5 Swimlanes Stacked Top to Bottom in Date Order */}
      <Stack gap="md">
        {LANES.map((lane) => {
          const isOpen = lane.status === 'OPEN';

          return (
            <Card
              key={lane.id}
              withBorder
              padding="md"
              radius="md"
              style={{
                border: isOpen ? '2px solid var(--mantine-color-red-6)' : '1px solid var(--mantine-color-default-border)',
                background: isOpen ? 'rgba(192, 57, 43, 0.04)' : undefined,
              }}
            >
              {/* Lane Header */}
              <Group justify="space-between" mb="sm">
                <div>
                  <Group gap="xs">
                    <Badge color="gray" size="xs" variant="outline">Lane {lane.id}</Badge>
                    <Text fw={700} size="sm" c={isOpen ? 'red' : undefined}>{lane.code}</Text>
                    <Badge
                      size="xs"
                      color={isOpen ? 'red' : lane.status === 'RESOLVED' ? 'green' : 'blue'}
                      variant={isOpen ? 'filled' : 'light'}
                    >
                      {lane.status}
                    </Badge>
                    <Text size="xs" c="dimmed">· {lane.title}</Text>
                  </Group>
                  <Text size="xs" c="dimmed" mt={2}>
                    {lane.element} ({lane.model}) · {lane.site} · {lane.date} · Duration: {lane.duration}
                  </Text>
                </div>

                {isOpen && onSelectIncident && (
                  <Button
                    size="xs"
                    color="red"
                    variant="light"
                    onClick={() => onSelectIncident(lane.code)}
                    leftSection={<IconArrowRight size={14} />}
                  >
                    Troubleshoot Incident
                  </Button>
                )}
              </Group>

              {/* Horizontal Sequence Flow */}
              <Box style={{ overflowX: 'auto', paddingBottom: 8 }}>
                <Group gap="xs" wrap="nowrap" align="center">
                  {lane.steps.map((step, sIdx) => {
                    const style = getStepBg(step.type);

                    return (
                      <Group key={sIdx} gap="xs" wrap="nowrap" align="center">
                        <Paper
                          p="xs"
                          radius="sm"
                          style={{
                            minWidth: 120,
                            background: style.bg,
                            border: `1px ${style.dashed ? 'dashed' : 'solid'} ${style.border}`,
                            color: style.color,
                            boxShadow: style.bold ? '0 0 0 1px #a8660b' : undefined,
                          }}
                        >
                          <Text size="xs" fw={700} style={{ color: style.color }}>
                            {step.time}
                          </Text>
                          <Text size="xs" style={{ color: style.color, lineHeight: 1.2 }} mt={2}>
                            {step.label}
                          </Text>
                        </Paper>

                        {/* Arrow with Wait Annotation */}
                        {sIdx < lane.steps.length - 1 && (
                          <Stack gap={2} align="center" style={{ minWidth: 60 }}>
                            {step.wait && (
                              <Badge size="xs" color="orange" variant="light" style={{ whiteSpace: 'nowrap' }}>
                                ⏱ {step.wait}
                              </Badge>
                            )}
                            <Text size="xs" c="dimmed">→</Text>
                          </Stack>
                        )}
                      </Group>
                    );
                  })}
                </Group>
              </Box>

              {/* Linked Knowledge Hexagon Card */}
              <Box mt="xs" pt="xs" style={{ borderTop: '1px dashed var(--mantine-color-default-border)' }}>
                <Group justify="space-between" align="flex-start">
                  <Group gap="xs">
                    <Badge
                      color={lane.knowledge.type === 'known' ? 'green' : lane.knowledge.type === 'disputed' ? 'orange' : 'red'}
                      size="sm"
                      variant="filled"
                    >
                      ⬡ {lane.knowledge.id} · {lane.knowledge.title}
                    </Badge>
                    <Text size="xs" fw={500}>{lane.knowledge.detail}</Text>
                  </Group>
                  <Text size="xs" c="dimmed" style={{ whiteSpace: 'nowrap' }}>
                    Source: {lane.knowledge.source}
                  </Text>
                </Group>
              </Box>
            </Card>
          );
        })}
      </Stack>
    </Stack>
  );
}

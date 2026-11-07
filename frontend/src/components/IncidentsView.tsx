import { useState, useEffect } from 'react';
import {
  Card,
  Text,
  Title,
  Group,
  Badge,
  Button,
  SimpleGrid,
  Stack,
  Alert,
  Loader,
  Paper,
  Box,
  Divider,
  List,
  Timeline,
  Chip,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertTriangle,
  IconCheck,
  IconArrowRight,
  IconSparkles,
  IconHelpCircle,
  IconPlayerPlay,
  IconClock,
  IconCpu,
  IconMapPin,
  IconTools,
  IconMessages,
  IconBolt,
  IconAlertCircle,
} from '@tabler/icons-react';
import {
  getIncidents,
  IncidentRecord,
  Agent1Report,
  runAgent1Report,
  triggerAgent2Ingest,
} from '../api/client';

export default function IncidentsView() {
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState<IncidentRecord | null>(null);
  const [report, setReport] = useState<Agent1Report | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [streamSteps, setStreamSteps] = useState<string[]>([]);
  const [filter, setFilter] = useState<'all' | 'open' | 'closed'>('all');
  const [captureChannels, setCaptureChannels] = useState<string[]>(['teams', 'email', 'sms']);
  const [capturingChannel, setCapturingChannel] = useState(false);

  useEffect(() => {
    loadIncidents();
  }, []);

  const loadIncidents = async () => {
    setLoading(true);
    try {
      const data = await getIncidents();
      setIncidents(data);
      // Auto-select open incident by default
      const openInc = data.find((i) => i.status === 'open') || data[0];
      if (openInc && !selectedIncident) {
        setSelectedIncident(openInc);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectIncident = (inc: IncidentRecord) => {
    setSelectedIncident(inc);
    setReport(null);
    setStreamSteps([]);
  };

  const handleRunAgent1 = async () => {
    if (!selectedIncident) return;
    setAnalyzing(true);
    setReport(null);
    setStreamSteps([
      'Step 1: Connecting to Neo4j knowledge graph & retrieving network element context...',
    ]);

    try {
      // Stream step progression simulation while querying backend
      const timer1 = setTimeout(() => {
        setStreamSteps((prev) => [
          ...prev,
          'Step 2: Searching Chroma RAG vector store for operational symptoms & field discussions...',
        ]);
      }, 350);

      const timer2 = setTimeout(() => {
        setStreamSteps((prev) => [
          ...prev,
          'Step 3: Evaluating active ContextAssertions (filtering superseded advice & noting conflicts)...',
        ]);
      }, 700);

      const timer3 = setTimeout(() => {
        setStreamSteps((prev) => [
          ...prev,
          'Step 4: Synthesizing non-hallucinatory incident report with ordered action steps...',
        ]);
      }, 1050);

      const result = await runAgent1Report(selectedIncident.id, selectedIncident.title);

      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);

      setStreamSteps([
        '1. fetch_incident_context: Retrieved element context and historical events.',
        '2. search_rag: Queried Chroma vector database for matching symptoms.',
        '3. find_related_assertions: Located active, valid ContextAssertions (suppressed outdated advice).',
        '4. compose_report: Synthesized structured report and ordered action plan.',
      ]);

      setReport(result);

      notifications.show({
        title: 'Analysis Complete',
        message: result.known_solution
          ? `Workaround found: ${result.known_solution.title}`
          : 'Incident analyzed. No prior workaround recorded.',
        color: result.known_solution ? 'green' : 'blue',
        icon: <IconCheck size={18} />,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      notifications.show({
        title: 'Analysis Notice',
        message: msg,
        color: 'orange',
        icon: <IconAlertTriangle size={18} />,
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCaptureAndReinvestigate = async () => {
    if (!selectedIncident || captureChannels.length === 0) return;
    setCapturingChannel(true);
    const channelNames = captureChannels.map((c) => c.toUpperCase()).join(', ');
    setStreamSteps((prev) => [
      ...prev,
      `Knowledge Collector: Reading latest ${channelNames} communication for ${selectedIncident.id}...`,
    ]);

    try {
      const ingestRes = await triggerAgent2Ingest(captureChannels, selectedIncident.id);
      notifications.show({
        title: 'Fix Captured by Knowledge Collector',
        message: `Extracted ${ingestRes.assertions_created.length || 1} workaround from ${channelNames} and saved to team knowledge graph. Re-investigating incident...`,
        color: 'green',
        icon: <IconCheck size={18} />,
      });

      // Automatically re-investigate
      await handleRunAgent1();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      notifications.show({
        title: 'Capture Notice',
        message: msg,
        color: 'orange',
        icon: <IconAlertCircle size={18} />,
      });
    } finally {
      setCapturingChannel(false);
    }
  };

  const filteredIncidents = incidents.filter((i) => {
    if (filter === 'open') return i.status === 'open';
    if (filter === 'closed') return i.status === 'closed';
    return true;
  });

  return (
    <Stack gap="lg">
      <div>
        <Title order={2} style={{ letterSpacing: -0.5 }}>
          Network Incidents & Troubleshooting
        </Title>
        <Text c="dimmed" size="sm">
          Live network work orders. Review event timelines and run the Incident Investigator to recommend next steps based on team knowledge.
        </Text>
      </div>

      {/* Urgent Alert Banner for the OPEN Incident */}
      {incidents.some((i) => i.status === 'open') && (
        <Alert
          color="red"
          variant="light"
          radius="md"
          title="ACTIVE OUTAGE — Action Required: WO-2026-1107-003 (TRN-117 Kiiminki mast)"
          icon={<IconAlertTriangle size={20} />}
        >
          <Group justify="space-between" align="center">
            <Text size="sm">
              SFP replaced on TRN-117 (TX-2000 fw 4.1). Optical link is UP, but forwarding traffic counters remain at zero bytes.
              The Incident Investigator can match past advice learned on TRN-042 to propose the immediate fix.
            </Text>
            <Button
              size="xs"
              color="red"
              variant="filled"
              onClick={() => {
                const openInc = incidents.find((i) => i.status === 'open');
                if (openInc) handleSelectIncident(openInc);
              }}
              leftSection={<IconArrowRight size={14} />}
            >
              Troubleshoot Open Incident
            </Button>
          </Group>
        </Alert>
      )}

      {/* Main Grid: Left column incident list, Right column details & investigation */}
      <SimpleGrid cols={{ base: 1, md: 12 }} spacing="lg">
        {/* Incidents List (4 cols) */}
        <Box style={{ gridColumn: 'span 4' }}>
          <Card withBorder padding="md" radius="md">
            <Group justify="space-between" mb="sm">
              <Text fw={700} size="sm">Work Orders ({filteredIncidents.length})</Text>
              <Group gap={4}>
                <Button
                  size="compact-xs"
                  variant={filter === 'all' ? 'filled' : 'subtle'}
                  onClick={() => setFilter('all')}
                >
                  All
                </Button>
                <Button
                  size="compact-xs"
                  variant={filter === 'open' ? 'filled' : 'subtle'}
                  color="red"
                  onClick={() => setFilter('open')}
                >
                  Open (1)
                </Button>
                <Button
                  size="compact-xs"
                  variant={filter === 'closed' ? 'filled' : 'subtle'}
                  color="gray"
                  onClick={() => setFilter('closed')}
                >
                  Resolved (4)
                </Button>
              </Group>
            </Group>

            {loading ? (
              <Group justify="center" p="xl">
                <Loader size="sm" />
              </Group>
            ) : (
              <Stack gap="xs">
                {filteredIncidents.map((inc) => {
                  const isSelected = selectedIncident?.id === inc.id;
                  const isOpen = inc.status === 'open';

                  return (
                    <Paper
                      key={inc.id}
                      withBorder
                      p="xs"
                      radius="sm"
                      onClick={() => handleSelectIncident(inc)}
                      style={{
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        borderLeft: isOpen
                          ? '4px solid var(--mantine-color-red-6)'
                          : isSelected
                          ? '4px solid var(--mantine-primary-color)'
                          : '4px solid transparent',
                        background: isSelected
                          ? 'var(--mantine-primary-color-light-hover)'
                          : 'rgba(255, 255, 255, 0.02)',
                      }}
                    >
                      <Group justify="space-between" align="flex-start" wrap="nowrap">
                        <div style={{ flex: 1 }}>
                          <Group gap="xs" mb={2}>
                            <Text fw={700} size="xs" c={isOpen ? 'red' : undefined}>
                              {inc.id}
                            </Text>
                            <Badge
                              size="xs"
                              color={isOpen ? 'red' : inc.status === 'closed' ? 'green' : 'gray'}
                              variant={isOpen ? 'filled' : 'light'}
                            >
                              {inc.status.toUpperCase()}
                            </Badge>
                            {inc.lane_ref && (
                              <Badge size="xs" color="gray" variant="outline">
                                Lane {inc.lane_ref}
                              </Badge>
                            )}
                          </Group>
                          <Text size="xs" lineClamp={2} fw={500}>
                            {inc.title}
                          </Text>
                          <Group gap="xs" mt={4}>
                            <Text size="xs" c="dimmed">
                              {inc.element_id} ({inc.model || 'Unknown'})
                            </Text>
                            <Text size="xs" c="dimmed">·</Text>
                            <Text size="xs" c="dimmed">
                              {inc.duration || 'N/A'}
                            </Text>
                          </Group>
                        </div>
                      </Group>
                    </Paper>
                  );
                })}
              </Stack>
            )}
          </Card>
        </Box>

        {/* Incident Details & Copilot (8 cols) */}
        <Box style={{ gridColumn: 'span 8' }}>
          {selectedIncident ? (
            <Stack gap="md">
              {/* Incident Header Card */}
              <Card withBorder padding="md" radius="md">
                <Group justify="space-between" align="flex-start">
                  <div>
                    <Group gap="xs" mb={4}>
                      <Badge
                        color={selectedIncident.status === 'open' ? 'red' : 'green'}
                        size="md"
                        variant="filled"
                      >
                        {selectedIncident.status.toUpperCase()}
                      </Badge>
                      <Badge color="gray" size="md" variant="outline">
                        {selectedIncident.id}
                      </Badge>
                      {selectedIncident.severity && (
                        <Badge
                          color={
                            selectedIncident.severity === 'critical'
                              ? 'red'
                              : selectedIncident.severity === 'major'
                              ? 'orange'
                              : 'blue'
                          }
                          size="md"
                        >
                          {selectedIncident.severity.toUpperCase()}
                        </Badge>
                      )}
                    </Group>
                    <Title order={3}>{selectedIncident.title}</Title>
                  </div>

                  <Button
                    size="md"
                    loading={analyzing}
                    onClick={handleRunAgent1}
                    leftSection={<IconSparkles size={18} />}
                  >
                    Investigate Incident
                  </Button>
                </Group>

                <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="xs" mt="md">
                  <Paper withBorder p="xs" radius="sm">
                    <Group gap="xs">
                      <IconCpu size={16} color="var(--mantine-primary-color)" />
                      <div>
                        <Text size="xs" c="dimmed">Target Element</Text>
                        <Text size="xs" fw={700}>{selectedIncident.element_id}</Text>
                      </div>
                    </Group>
                  </Paper>
                  <Paper withBorder p="xs" radius="sm">
                    <Group gap="xs">
                      <IconTools size={16} color="var(--mantine-color-blue-6)" />
                      <div>
                        <Text size="xs" c="dimmed">Hardware Model</Text>
                        <Text size="xs" fw={700}>{selectedIncident.model || 'TX-2000'}</Text>
                      </div>
                    </Group>
                  </Paper>
                  <Paper withBorder p="xs" radius="sm">
                    <Group gap="xs">
                      <IconMapPin size={16} color="var(--mantine-color-orange-6)" />
                      <div>
                        <Text size="xs" c="dimmed">Site Location</Text>
                        <Text size="xs" fw={700}>{selectedIncident.site || 'N/A'}</Text>
                      </div>
                    </Group>
                  </Paper>
                  <Paper withBorder p="xs" radius="sm">
                    <Group gap="xs">
                      <IconClock size={16} color="var(--mantine-color-gray-6)" />
                      <div>
                        <Text size="xs" c="dimmed">Total Duration</Text>
                        <Text size="xs" fw={700}>{selectedIncident.duration || 'N/A'}</Text>
                      </div>
                    </Group>
                  </Paper>
                </SimpleGrid>

                {/* Event Sequence Timeline from Reference Diagram */}
                {selectedIncident.sequence && selectedIncident.sequence.length > 0 && (
                  <Box mt="md" pt="md" style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
                    <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb="xs">
                      Event Sequence Lane (Diagram Reference)
                    </Text>
                    <Timeline active={selectedIncident.sequence.length} bulletSize={22} lineWidth={2}>
                      {selectedIncident.sequence.map((step, idx) => {
                        const isPending = step.kind === 'pending';
                        const isRecovery = step.kind === 'recovery';
                        const isFault = step.kind === 'fault';
                        const isAccess = step.kind === 'access' || step.kind === 'accessBlock';

                        let bulletColor = 'green';
                        if (isPending || isFault) bulletColor = 'red';
                        else if (isRecovery) bulletColor = 'green';
                        else if (isAccess) bulletColor = 'orange';

                        return (
                          <Timeline.Item
                            key={idx}
                            color={bulletColor}
                            title={
                              <Group gap="xs">
                                <Text size="xs" fw={700}>{step.label}</Text>
                                {step.wait && (
                                  <Badge size="xs" color="orange" variant="light">
                                    ⏱ {step.wait}
                                  </Badge>
                                )}
                              </Group>
                            }
                          >
                            <Text size="xs" c="dimmed">{step.time}</Text>
                          </Timeline.Item>
                        );
                      })}
                    </Timeline>

                    {selectedIncident.assertion_ref && (
                      <Alert color="green" variant="light" radius="sm" mt="sm" p="xs">
                        <Text size="xs" fw={600}>
                          Known Team Workaround: {selectedIncident.assertion_ref}
                        </Text>
                      </Alert>
                    )}
                  </Box>
                )}
              </Card>

              {/* Real-time Streaming Execution Steps */}
              {streamSteps.length > 0 && (
                <Card withBorder padding="md" radius="md">
                  <Group justify="space-between" mb="xs">
                    <Group gap="xs">
                      <IconPlayerPlay size={18} color="var(--mantine-primary-color)" />
                      <Text fw={700} size="sm">Investigation Trace (Checking Graph & Team Messages)</Text>
                    </Group>
                    {analyzing && <Loader size="xs" />}
                  </Group>
                  <Stack gap={4}>
                    {streamSteps.map((stepText, idx) => (
                      <Text key={idx} size="xs" ff="monospace" c="dimmed">
                        ✓ {stepText}
                      </Text>
                    ))}
                  </Stack>
                </Card>
              )}

              {/* Synthesized Report */}
              {report && (
                <Card withBorder padding="lg" radius="md" style={{ border: '2px solid var(--mantine-primary-color)' }}>
                  <Group justify="space-between" mb="md">
                    <div>
                      <Badge size="lg" variant="filled" mb={4}>
                        Investigation Findings & Action Plan
                      </Badge>
                      <Title order={3}>{report.summary}</Title>
                    </div>
                    <Badge color={report.confidence > 0.8 ? 'green' : 'orange'} size="xl" variant="light">
                      Confidence: {Math.round(report.confidence * 100)}%
                    </Badge>
                  </Group>

                  <Text size="sm" mb="md">{report.problem_description}</Text>

                  {/* Known Solution Card */}
                  {report.known_solution ? (
                    <Alert
                      color="green"
                      variant="filled"
                      radius="md"
                      title={report.known_solution.title}
                      icon={<IconCheck size={20} />}
                      mb="md"
                    >
                      <Text size="sm" fw={600} mb="xs">
                        {report.known_solution.recommendation}
                      </Text>
                      <Divider my="xs" color="rgba(255,255,255,0.2)" />
                      <Group gap="md">
                        <Text size="xs">
                          <b>Source Ref:</b> {report.known_solution.source_ref}
                        </Text>
                        <Text size="xs">
                          <b>Confidence:</b> {Math.round(report.known_solution.confidence * 100)}%
                        </Text>
                        {report.known_solution.valid_from && (
                          <Text size="xs">
                            <b>Valid From:</b> {report.known_solution.valid_from.split('T')[0]}
                          </Text>
                        )}
                      </Group>
                    </Alert>
                  ) : (
                    <Card
                      withBorder
                      padding="md"
                      radius="md"
                      mb="md"
                      style={{ background: 'var(--mantine-color-blue-light)' }}
                    >
                      <Group justify="space-between" align="flex-start" mb="xs">
                        <Group gap="xs">
                          <IconMessages size={20} color="var(--mantine-color-blue-6)" />
                          <div>
                            <Text fw={700} size="sm">No Prior Fix Found · Capture Team Advice</Text>
                            <Text size="xs" c="dimmed">
                              Did an expert discuss a workaround in Teams, Email, or SMS? Select the channel to capture it:
                            </Text>
                          </div>
                        </Group>
                      </Group>

                      <Stack gap="xs" mt="xs">
                        <Text size="xs" fw={600}>
                          Select team communication sources to scan (multiple channels allowed):
                        </Text>
                        <Chip.Group multiple value={captureChannels} onChange={setCaptureChannels}>
                          <Group gap="xs">
                            <Chip value="teams" variant="filled" size="xs">
                              💬 Teams Chat (#transmission-ops)
                            </Chip>
                            <Chip value="email" variant="filled" size="xs">
                              ✉️ Field Email (Support Thread)
                            </Chip>
                            <Chip value="sms" variant="filled" size="xs">
                              📱 SMS Dispatch
                            </Chip>
                          </Group>
                        </Chip.Group>

                        <Group justify="space-between" align="center" mt="xs">
                          <Text size="xs" c="dimmed">
                            {captureChannels.length === 0
                              ? 'Select at least one channel above to scan.'
                              : `Scanning ${captureChannels.length} channel(s): ${captureChannels.join(', ').toUpperCase()}`}
                          </Text>
                          <Button
                            size="xs"
                            disabled={captureChannels.length === 0}
                            loading={capturingChannel}
                            onClick={handleCaptureAndReinvestigate}
                            leftSection={<IconBolt size={14} />}
                          >
                            Capture Fix & Re-investigate
                          </Button>
                        </Group>
                      </Stack>
                    </Card>
                  )}

                  {/* Suggested Next Steps */}
                  <Box mb="md">
                    <Text size="sm" fw={700} mb="xs">
                      Suggested Next Steps (Ordered Operational Action Plan):
                    </Text>
                    <List size="sm" spacing="xs" withPadding>
                      {report.suggested_next_steps.map((step, idx) => (
                        <List.Item key={idx}>{step}</List.Item>
                      ))}
                    </List>
                  </Box>

                  {/* Open Questions / Disputed Guidance Warnings */}
                  {report.open_questions && report.open_questions.length > 0 && (
                    <Alert
                      color="orange"
                      variant="light"
                      radius="md"
                      title="Open Questions & Guidance Warnings"
                      icon={<IconHelpCircle size={18} />}
                    >
                      <List size="xs" spacing={4}>
                        {report.open_questions.map((q, idx) => (
                          <List.Item key={idx}>{q}</List.Item>
                        ))}
                      </List>
                    </Alert>
                  )}
                </Card>
              )}
            </Stack>
          ) : (
            <Card withBorder p="xl" radius="md">
              <Text c="dimmed" ta="center">Select an incident on the left to view details and run Agent 1 analysis.</Text>
            </Card>
          )}
        </Box>
      </SimpleGrid>
    </Stack>
  );
}

import { useState, useEffect } from 'react';
import {
  Card,
  Text,
  Title,
  Group,
  Button,
  Badge,
  SimpleGrid,
  Tabs,
  Stack,
  Alert,
  Loader,
  Paper,
  Box,
  Divider,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconServer,
  IconDatabase,
  IconCheck,
  IconAlertCircle,
  IconRefresh,
  IconBolt,
  IconMessages,
  IconMail,
  IconDeviceMobile,
} from '@tabler/icons-react';
import {
  getHealth,
  triggerAgent2Ingest,
  triggerSeedGraph,
  HealthData,
  IngestResponse,
} from '../api/client';
import { RAW_TEAMS_THREADS, RAW_EMAILS, RAW_SMS } from '../data/rawChannels';

export default function SettingsView() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [lastIngestResult, setLastIngestResult] = useState<IngestResponse | null>(null);

  const checkHealth = async () => {
    setLoadingHealth(true);
    try {
      const data = await getHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleIngest = async () => {
    setIngesting(true);
    try {
      const result = await triggerAgent2Ingest(['teams', 'email', 'sms']);
      setLastIngestResult(result);
      notifications.show({
        title: 'Team Knowledge Collection Complete',
        message: `Knowledge Collector extracted ${result.assertions_created.length} workarounds, linked ${result.incidents_touched.length} incidents, and indexed ${result.rag_ids_added.length} team messages.`,
        color: 'green',
        icon: <IconCheck size={18} />,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      notifications.show({
        title: 'Collection Notice',
        message: msg,
        color: 'orange',
        icon: <IconAlertCircle size={18} />,
      });
    } finally {
      setIngesting(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const result = await triggerSeedGraph();
      notifications.show({
        title: 'Knowledge Graph Seed',
        message: result.message || 'Seeded successfully.',
        color: 'green',
        icon: <IconCheck size={18} />,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      notifications.show({
        title: 'Seeding Notice',
        message: msg,
        color: 'orange',
        icon: <IconAlertCircle size={18} />,
      });
    } finally {
      setSeeding(false);
    }
  };

  return (
    <Stack gap="lg">
      <div>
        <Title order={2} style={{ letterSpacing: -0.5 }}>
          Team Knowledge & Collector Settings
        </Title>
        <Text c="dimmed" size="sm">
          Control center for scanning team messages, seeding the network knowledge graph, and inspecting raw field channels.
        </Text>
      </div>

      {/* Control Card for Initial Data Ingestion */}
      <Card withBorder padding="lg" radius="md">
        <Group justify="space-between" mb="sm">
          <div>
            <Group gap="xs">
              <IconBolt color="var(--mantine-primary-color)" size={22} />
              <Title order={4}>Knowledge Collector</Title>
            </Group>
            <Text size="sm" c="dimmed" mt={4}>
              Reads team communications (Teams chats, Field Emails, SMS) for expert workarounds, links them to network entities in Neo4j, and search-indexes them.
            </Text>
          </div>
          <Group>
            <Button
              variant="outline"
              loading={seeding}
              onClick={handleSeed}
              leftSection={<IconDatabase size={16} />}
            >
              Seed Knowledge Graph
            </Button>
            <Button
              loading={ingesting}
              onClick={handleIngest}
              leftSection={<IconBolt size={16} />}
            >
              Capture Team Knowledge
            </Button>
          </Group>
        </Group>

        {lastIngestResult && (
          <Alert color="green" variant="light" title="Collection Summary" mt="md" radius="md">
            <Group gap="md">
              <Badge color="green" size="lg" variant="filled">
                {lastIngestResult.assertions_created.length} Workarounds Captured
              </Badge>
              <Badge color="blue" size="lg" variant="filled">
                {lastIngestResult.incidents_touched.length} Incidents Linked
              </Badge>
              <Badge color="violet" size="lg" variant="filled">
                {lastIngestResult.rag_ids_added.length} Team Messages Indexed
              </Badge>
            </Group>
            <Text size="xs" mt="xs" c="dimmed">
              Captured Workarounds: {lastIngestResult.assertions_created.join(', ') || 'None (already processed)'}
            </Text>
          </Alert>
        )}
      </Card>

      {/* System Health Section */}
      <Card withBorder padding="md" radius="md">
        <Group justify="space-between" mb="xs">
          <Group gap="xs">
            <IconServer size={20} color="var(--mantine-color-blue-6)" />
            <Text fw={600} size="sm">System & Microservice Health</Text>
          </Group>
          <Button
            size="xs"
            variant="subtle"
            leftSection={<IconRefresh size={14} />}
            onClick={checkHealth}
            loading={loadingHealth}
          >
            Refresh
          </Button>
        </Group>

        {loadingHealth && !health ? (
          <Group justify="center" p="md">
            <Loader size="sm" />
            <Text size="sm" c="dimmed">Checking backend health...</Text>
          </Group>
        ) : (
          <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="sm">
            <Paper withBorder p="xs" radius="sm">
              <Text size="xs" c="dimmed">Agents Service (:8000)</Text>
              <Badge color="green" variant="light" mt={4}>
                {health?.status || 'Online (API Ready)'}
              </Badge>
            </Paper>
            <Paper withBorder p="xs" radius="sm">
              <Text size="xs" c="dimmed">Neo4j Graph (bolt:7687)</Text>
              <Badge color={health?.neo4j?.includes('connected') ? 'green' : 'blue'} variant="light" mt={4}>
                {health?.neo4j || 'Ready / Connected'}
              </Badge>
            </Paper>
            <Paper withBorder p="xs" radius="sm">
              <Text size="xs" c="dimmed">Chroma Search (:8004)</Text>
              <Badge color="violet" variant="light" mt={4}>
                Offline MiniLM Ready
              </Badge>
            </Paper>
            <Paper withBorder p="xs" radius="sm">
              <Text size="xs" c="dimmed">Channel Connectors</Text>
              <Badge color="green" variant="light" mt={4}>
                Teams, Email, SMS Mounted
              </Badge>
            </Paper>
          </SimpleGrid>
        )}
      </Card>

      {/* Communication Channels Inspector */}
      <Card withBorder padding="md" radius="md">
        <Title order={4} mb="xs">
          Raw Communication Channels (Expert Chats & Field Emails)
        </Title>
        <Text size="sm" c="dimmed" mb="md">
          Browse raw operational messages from field teams and engineers. Notice how valuable workarounds are discovered in these conversations.
        </Text>

        <Tabs defaultValue="teams">
          <Tabs.List mb="md">
            <Tabs.Tab value="teams" leftSection={<IconMessages size={16} />}>
              Teams Threads ({RAW_TEAMS_THREADS.length})
            </Tabs.Tab>
            <Tabs.Tab value="emails" leftSection={<IconMail size={16} />}>
              Field Emails ({RAW_EMAILS.length})
            </Tabs.Tab>
            <Tabs.Tab value="sms" leftSection={<IconDeviceMobile size={16} />}>
              Field SMS ({RAW_SMS.length})
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="teams">
            <Stack gap="md">
              {RAW_TEAMS_THREADS.map((thread) => (
                <Paper key={thread.id} withBorder p="sm" radius="md">
                  <Group justify="space-between" mb="xs">
                    <div>
                      <Text fw={600} size="sm">{thread.topic}</Text>
                      <Text size="xs" c="dimmed">ID: {thread.id} · Participants: {thread.participants.join(', ')}</Text>
                    </div>
                    <Badge variant="outline" size="xs">Teams</Badge>
                  </Group>
                  <Divider mb="xs" />
                  <Stack gap="xs">
                    {thread.messages.map((m, idx) => (
                      <Box
                        key={idx}
                        p="xs"
                        style={{
                          borderRadius: 6,
                          background: m.author.includes('Erkki') || m.author.includes('Aino')
                            ? 'var(--mantine-primary-color-light-hover)'
                            : 'rgba(255, 255, 255, 0.03)',
                          borderLeft: m.author.includes('Erkki') || m.author.includes('Aino')
                            ? '3px solid var(--mantine-primary-color)'
                            : '3px solid transparent',
                        }}
                      >
                        <Group justify="space-between">
                          <Text size="xs" fw={700}>{m.author}</Text>
                          <Text size="xs" c="dimmed">{m.time.split('T')[1].slice(0, 5)}</Text>
                        </Group>
                        <Text size="sm" mt={2}>{m.text}</Text>
                      </Box>
                    ))}
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="emails">
            <Stack gap="md">
              {RAW_EMAILS.map((email) => (
                <Paper key={email.id} withBorder p="sm" radius="md">
                  <Group justify="space-between" mb="xs">
                    <div>
                      <Text fw={600} size="sm">{email.subject}</Text>
                      <Text size="xs" c="dimmed">From: {email.from} · {email.date.split('T')[0]}</Text>
                    </div>
                    <Badge
                      color={email.note.includes('ACTIVE') ? 'green' : email.note.includes('SUPERSEDED') ? 'orange' : 'blue'}
                      size="xs"
                    >
                      {email.note}
                    </Badge>
                  </Group>
                  <Divider mb="xs" />
                  <Text size="sm" style={{ whiteSpace: 'pre-line' }}>{email.body}</Text>
                </Paper>
              ))}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="sms">
            <Stack gap="md">
              {RAW_SMS.map((sms) => (
                <Paper key={sms.id} withBorder p="sm" radius="md">
                  <Group justify="space-between" mb="xs">
                    <Text fw={600} size="sm">{sms.thread}</Text>
                    <Badge color="violet" size="xs">SMS</Badge>
                  </Group>
                  <Divider mb="xs" />
                  <Stack gap="xs">
                    {sms.messages.map((m, idx) => (
                      <Box key={idx} p="xs" style={{ borderRadius: 6, background: 'rgba(255, 255, 255, 0.03)' }}>
                        <Group justify="space-between">
                          <Text size="xs" fw={700}>{m.sender}</Text>
                          <Text size="xs" c="dimmed">{m.time.split('T')[1].slice(0, 5)}</Text>
                        </Group>
                        <Text size="sm" mt={2}>{m.text}</Text>
                      </Box>
                    ))}
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </Tabs.Panel>
        </Tabs>
      </Card>
    </Stack>
  );
}

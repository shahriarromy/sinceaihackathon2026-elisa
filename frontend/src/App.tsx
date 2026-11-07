import { useState } from 'react';
import {
  AppShell,
  Burger,
  Group,
  NavLink,
  Title,
  Text,
  Badge,
  ActionIcon,
  useMantineColorScheme,
  Box,
  ThemeIcon,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconAlertTriangle, IconTimeline, IconSettings, IconSun, IconMoon, IconNetwork } from '@tabler/icons-react';
import SettingsView from './components/SettingsView';
import IncidentsView from './components/IncidentsView';
import SequencesFlowView from './components/SequencesFlowView';

export type NavTab = 'incidents' | 'sequences' | 'settings';

export default function App() {
  const [opened, { toggle }] = useDisclosure();
  const [activeTab, setActiveTab] = useState<NavTab>('incidents');
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 280, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <ThemeIcon size="lg" radius="md">
              <IconNetwork size={22} />
            </ThemeIcon>
            <div>
              <Title order={4} style={{ letterSpacing: -0.5 }}>
                Network Operations · Team Knowledge
              </Title>
              <Text size="xs" c="dimmed">
                Field Knowledge Capture & Incident Troubleshooting · Elisa Operations
              </Text>
            </div>
          </Group>

          <Group>
            <Badge variant="dot" color="green" size="md">
              Backend Connected
            </Badge>
            <ActionIcon
              variant="default"
              size="lg"
              aria-label="Toggle color scheme"
              onClick={() => toggleColorScheme()}
            >
              {colorScheme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}
            </ActionIcon>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb="xs">
          Operations Center
        </Text>

        <NavLink
          label="Incidents & Investigation"
          description="Live work orders & investigator"
          leftSection={<IconAlertTriangle size={20} stroke={1.5} />}
          active={activeTab === 'incidents'}
          onClick={() => {
            setActiveTab('incidents');
            if (opened) toggle();
          }}
          variant="filled"
          mb={4}
        />

        <NavLink
          label="Resolution Timelines"
          description="5 Work order reference flows"
          leftSection={<IconTimeline size={20} stroke={1.5} />}
          active={activeTab === 'sequences'}
          onClick={() => {
            setActiveTab('sequences');
            if (opened) toggle();
          }}
          variant="filled"
          mb={4}
        />

        <NavLink
          label="Knowledge Collector"
          description="Teams, email & SMS channels"
          leftSection={<IconSettings size={20} stroke={1.5} />}
          active={activeTab === 'settings'}
          onClick={() => {
            setActiveTab('settings');
            if (opened) toggle();
          }}
          variant="filled"
        />

        <Box mt="auto" pt="md" style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
          <Text size="xs" c="dimmed">
            TRN-042 / TRN-117 SFP Swap & SAL-03 Barrier Scenarios
          </Text>
        </Box>
      </AppShell.Navbar>

      <AppShell.Main>
        <Box p="xs">
          {activeTab === 'incidents' && <IncidentsView />}

          {activeTab === 'sequences' && (
            <SequencesFlowView onSelectIncident={() => setActiveTab('incidents')} />
          )}

          {activeTab === 'settings' && <SettingsView />}
        </Box>
      </AppShell.Main>
    </AppShell>
  );
}

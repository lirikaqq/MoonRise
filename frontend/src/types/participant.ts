export interface ParticipantData {
  id: number;
  user_id: number;
  display_name: string;
  discord_tag: string;
  battle_tag: string;
  primary_role: 'tank' | 'dps' | 'sup' | 'support' | 'flex';
  secondary_role: 'tank' | 'dps' | 'sup' | 'support' | 'flex';
  bio: string;
  notes: string;
  rank: string | null;
  avatar_url: string | null;
  is_captain: boolean;
  is_allowed: boolean;
  status: string;
  submitted_at: string;
  application_data?: Record<string, unknown>;
}
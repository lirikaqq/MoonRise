// src/pages/PlayerProfilePage.jsx
import React from 'react';
import { useParams } from 'react-router-dom';

import PlayerProfile from '../components/player_profile/PlayerProfile';

export default function PlayerProfilePage() {
  const { id } = useParams();

  if (!id) {
    return <div>Player ID not found in URL</div>;
  }

  return <PlayerProfile playerId={parseInt(id, 10)} />;
}
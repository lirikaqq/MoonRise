import { useState, useEffect, useCallback, useRef } from 'react';
import { draftApi } from '../api/draft';

export function useDraft(sessionId) {
  const [draftState, setDraftState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [completedTeams, setCompletedTeams] = useState(null);

  const websocket = useRef(null);

  // --- Загрузка начального состояния ---
  useEffect(() => {
    if (!sessionId) return;

    setLoading(true);
    draftApi.getState(sessionId)
      .then(initialState => {
        setDraftState(initialState);
      })
      .catch(err => {
        setError('Failed to load draft state.');
        console.error(err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [sessionId]);

  // --- WebSocket подключение ---
  useEffect(() => {
    if (!sessionId || draftState?.status === 'completed') return;

    const token = localStorage.getItem('moonrise_token');
    if (!token) {
        setError("Authentication token not found.");
        return;
    }

    const wsUrl = `ws://localhost:8000/ws/draft/${sessionId}?token=${token}`;
    websocket.current = new WebSocket(wsUrl);

    websocket.current.onopen = () => {
      console.log('✅ WebSocket Connected');
      setIsConnected(true);
    };

    websocket.current.onclose = () => {
      console.log('❌ WebSocket Disconnected');
      setIsConnected(false);
    };

    websocket.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('📥 WS Message Received:', message);

      if (message.type === 'pick_made') {
        const rawData = message.data;

        // Преобразуем данные из WS-события в нужный формат
        const newPick = {
            pick_number: rawData.pick_number,
            round_number: rawData.round_number,
            captain_id: rawData.team_id, // Бэкенд шлет ID команды (капитана) в поле team_id
            team_name: rawData.team_name || "Unknown",
            picked_user_id: rawData.picked_user_id,
            picked_user_name: rawData.picked_user_name,
            assigned_role: rawData.assigned_role
        };

        setDraftState(prevState => {
          if (!prevState) return prevState;

          const updatedPicks = [...prevState.picks, newPick];
          const updatedPlayerPool = prevState.player_pool.filter(
            p => p.user_id !== newPick.picked_user_id
          );

          return {
            ...prevState,
            picks: updatedPicks,
            player_pool: updatedPlayerPool,
            current_pick_index: prevState.current_pick_index + 1,
          };
        });
      }

      if (message.type === 'draft_completed') {
        const teamsData = message.data.teams || [];

        setDraftState(prevState => {
          if (!prevState) return prevState;
          return {
            ...prevState,
            status: 'completed',
          };
        });

        setCompletedTeams(teamsData);

        // Закрываем WebSocket — драфт завершён
        if (websocket.current) {
          websocket.current.close();
        }
      }

      if (message.type === 'draft_started') {
        // Обновляем статус на in_progress
        setDraftState(prevState => {
          if (!prevState) return prevState;
          return {
            ...prevState,
            status: 'in_progress',
          };
        });
      }
    };

    return () => {
      if (websocket.current) {
        websocket.current.close();
      }
    };
  }, [sessionId, draftState?.status]);


  // --- Функция для совершения пика ---
  const makePick = useCallback(async (pickData) => {
    if (!sessionId) {
      console.error('[useDraft] makePick called with no sessionId!');
      alert('Ошибка: сессия драфта не найдена.');
      return;
    }
    console.debug(`[useDraft] makePick: sessionId=${sessionId}, pickData=`, pickData);
    try {
      await draftApi.makePick(sessionId, pickData);
    } catch (err) {
      console.error("Failed to make a pick:", err);
      alert(err.response?.data?.detail || "Failed to make a pick.");
    }
  }, [sessionId]);

  // --- Функция для завершения драфта (админ) ---
  const completeDraft = useCallback(async () => {
    if (!sessionId) return;
    try {
      const result = await draftApi.completeDraft(sessionId);
      // Данные команд придут через WS-событие draft_completed
      // но если WS ещё не подключился — обработаем здесь
      if (result.teams) {
        setCompletedTeams(result.teams);
        setDraftState(prevState => {
          if (!prevState) return prevState;
          return { ...prevState, status: 'completed' };
        });
      }
      return result;
    } catch (err) {
      console.error("Failed to complete draft:", err);
      alert(err.response?.data?.detail || "Failed to complete draft.");
      throw err;
    }
  }, [sessionId]);

  return { draftState, loading, error, isConnected, makePick, completeDraft, completedTeams };
}
import React, { useState, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import './StageParticipantsManager.css';

/**
 * Универсальный менеджер управления участниками этапа.
 * - Для Round Robin: создание групп и drag-and-drop участников
 * - Для Elimination: упорядоченный список для посева
 */
export default function StageParticipantsManager({
  stage,
  participants = [],
  groups = [],
  onGroupCreate,
  onGroupDelete,
  onParticipantAssign,
  onBulkAssign,
  onReorder
}) {
  const [newGroupName, setNewGroupName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedParticipants, setSelectedParticipants] = useState([]);

  const isRoundRobin = stage.format === 'ROUND_ROBIN';
  const isElimination = ['SINGLE_ELIMINATION', 'DOUBLE_ELIMINATION'].includes(stage.format);

  // Фильтрация участников по поиску
  const filteredParticipants = participants.filter(p =>
    p.user?.username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.user?.display_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Добавление группы
  const handleAddGroup = () => {
    if (!newGroupName.trim()) {
      alert('Введите название группы!');
      return;
    }
    onGroupCreate(stage.id, newGroupName.trim());
    setNewGroupName('');
  };

  // Drag and Drop обработчик
  const handleOnDragEnd = useCallback((result) => {
    const { source, destination, draggableId } = result;

    // Если dropped outside
    if (!destination) return;

    // Если перемещение между группами
    if (source.droppableId !== destination.droppableId) {
      const participantId = parseInt(draggableId);
      const targetGroupId = destination.droppableId === 'unassigned' ? null : parseInt(destination.droppableId);

      onParticipantAssign(targetGroupId, participantId);
      return;
    }

    // Если перемещение внутри списка (reorder для elimination)
    if (isElimination && source.droppableId === 'seed-list') {
      onReorder(source.index, destination.index);
    }
  }, [isElimination, onParticipantAssign, onReorder]);

  // Выбор участника для массового назначения
  const toggleSelectParticipant = (participantId) => {
    setSelectedParticipants(prev =>
      prev.includes(participantId)
        ? prev.filter(id => id !== participantId)
        : [...prev, participantId]
    );
  };

  // Массовое назначение в группу
  const handleBulkAssign = (groupId) => {
    if (selectedParticipants.length === 0) {
      alert('Выберите участников!');
      return;
    }
    onBulkAssign(groupId, selectedParticipants);
    setSelectedParticipants([]);
  };

  return (
    <div className="spm-container">
      <h3 className="spm-title">Управление участниками этапа</h3>

      {/* Поиск */}
      <div className="spm-search">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Поиск участника..."
          className="spm-search-input"
        />
      </div>

      {/* Drag & Drop контекст */}
      <DragDropContext onDragEnd={handleOnDragEnd}>
        {isRoundRobin ? (
          // ROUND ROBIN: группы + неназначенные
          <div className="spm-round-robin-layout">
            {/* Неназначенные участники */}
            <div className="spm-unassigned-column">
              <h4>Неназначенные участники</h4>
              <Droppable droppableId="unassigned">
                {(provided) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className="spm-participants-list"
                  >
                    {filteredParticipants
                      .filter(p => !p.group_id)
                      .map((participant, index) => (
                        <Draggable
                          key={participant.id}
                          draggableId={String(participant.id)}
                          index={index}
                        >
                          {(provided) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className="spm-participant-card"
                            >
                              <div className="checkbox-wrapper">
                                <input
                                  type="checkbox"
                                  checked={selectedParticipants.includes(participant.id)}
                                  onChange={() => toggleSelectParticipant(participant.id)}
                                />
                              </div>
                              <div className="spm-participant-info">
                                <div className="spm-participant-name">
                                  {participant.user?.display_name || participant.user?.username || 'Unknown'}
                                </div>
                                <div className="spm-participant-seed">
                                  Seed: {participant.seed || '-'}
                                </div>
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>

              {/* Массовое назначение */}
              {selectedParticipants.length > 0 && (
                <div className="spm-bulk-actions">
                  <span>Выбрано: {selectedParticipants.length}</span>
                  {groups.map(group => (
                    <button
                      key={group.id}
                      onClick={() => handleBulkAssign(group.id)}
                      className="spm-bulk-btn"
                    >
                      В {group.name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Группы */}
            <div className="spm-groups-container">
              {groups.map(group => (
                <Droppable key={group.id} droppableId={String(group.id)}>
                  {(provided) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className="spm-group-card"
                    >
                      <div className="spm-group-header">
                        <h4>{group.name}</h4>
                        <button
                          onClick={() => onGroupDelete(group.id)}
                          className="spm-group-delete"
                        >
                          ✕
                        </button>
                      </div>
                      <div className="spm-group-participants">
                        {filteredParticipants
                          .filter(p => p.group_id === group.id)
                          .map((participant, index) => (
                            <Draggable
                              key={participant.id}
                              draggableId={String(participant.id)}
                              index={index}
                            >
                              {(provided) => (
                                <div
                                  ref={provided.innerRef}
                                  {...provided.draggableProps}
                                  {...provided.dragHandleProps}
                                  className="spm-participant-card assigned"
                                >
                                  <div className="spm-participant-info">
                                    <div className="spm-participant-name">
                                      {participant.user?.display_name || participant.user?.username || 'Unknown'}
                                    </div>
                                    <div className="spm-participant-seed">
                                      Seed: {participant.seed || index + 1}
                                    </div>
                                  </div>
                                </div>
                              )}
                            </Draggable>
                          ))}
                        {provided.placeholder}
                      </div>
                    </div>
                  )}
                </Droppable>
              ))}

              {/* Добавить группу */}
              <div className="spm-add-group">
                <input
                  type="text"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  placeholder="Название группы"
                  className="spm-add-group-input"
                />
                <button onClick={handleAddGroup} className="spm-add-group-btn">
                  + Добавить группу
                </button>
              </div>
            </div>
          </div>
        ) : isElimination ? (
          // ELIMINATION: упорядоченный список для посева
          <div className="spm-elimination-layout">
            <h4>Посев участников (перетащите для изменения порядка)</h4>
            <Droppable droppableId="seed-list">
              {(provided) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className="spm-seed-list"
                >
                  {filteredParticipants
                    .sort((a, b) => (a.seed || 999) - (b.seed || 999))
                    .map((participant, index) => (
                      <Draggable
                        key={participant.id}
                        draggableId={String(participant.id)}
                        index={index}
                      >
                        {(provided) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            className="spm-seed-item"
                          >
                            <div className="spm-seed-number">#{index + 1}</div>
                            <div className="spm-seed-info">
                              <div className="spm-seed-name">
                                {participant.user?.display_name || participant.user?.username || 'Unknown'}
                              </div>
                              <div className="spm-seed-meta">
                                Seed: {participant.seed || index + 1}
                              </div>
                            </div>
                          </div>
                        )}
                      </Draggable>
                    ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </div>
        ) : (
          // SWISS и другие форматы
          <div className="spm-generic-layout">
            <p>Для этого формата распределение участников настраивается автоматически.</p>
          </div>
        )}
      </DragDropContext>
    </div>
  );
}

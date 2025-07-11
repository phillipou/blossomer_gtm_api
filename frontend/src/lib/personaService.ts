import { apiFetch } from './apiClient';
import type { Persona, PersonaCreate, PersonaUpdate, TargetPersonaRequest, TargetPersonaResponse } from '../types/api';
import { transformKeysToCamelCase } from "./utils";

// =================================================================
// Persona CRUD API Functions
// =================================================================

export async function getPersonas(accountId: string, token?: string | null): Promise<Persona[]> {
  return apiFetch<Persona[]>(`/accounts/${accountId}/personas`, { method: 'GET' }, token);
}

export function normalizePersonaResponse(persona: Persona): Persona {
  console.log('[NORMALIZE] Raw persona response:', persona);
  const data = transformKeysToCamelCase<Record<string, any>>(persona.data || {});
  const normalized = {
    ...persona,
    ...data,
    data,
  };
  console.log('[NORMALIZE] Normalized persona:', normalized);
  return normalized;
}

export async function getPersona(personaId: string, token?: string | null): Promise<Persona> {
  const persona = await apiFetch<Persona>(`/personas/${personaId}`, { method: 'GET' }, token);
  return normalizePersonaResponse(persona);
}


export async function updatePersona(personaId: string, personaData: PersonaUpdate, token?: string | null): Promise<Persona> {
  return apiFetch<Persona>(`/personas/${personaId}`, {
    method: 'PUT',
    body: JSON.stringify(personaData),
  }, token);
}

export async function deletePersona(personaId: string, token?: string | null): Promise<void> {
  await apiFetch<void>(`/personas/${personaId}`, { method: 'DELETE' }, token);
}

export async function generatePersona(accountId: string, personaData: TargetPersonaRequest, token?: string | null): Promise<TargetPersonaResponse> {
    return apiFetch<TargetPersonaResponse>(`/accounts/${accountId}/personas/generate`, {
        method: 'POST',
        body: JSON.stringify(personaData),
    }, token);
}

// Helper to transform AI response format to backend CRUD format
function transformPersonaToCreateFormat(aiResponse: TargetPersonaResponse): PersonaCreate {
  return {
    name: aiResponse.targetPersonaName,
    data: aiResponse,
  };
}

export async function createPersona(accountId: string, personaData: TargetPersonaResponse, token?: string | null): Promise<Persona> {
  // Transform AI format to backend CRUD format
  const createData = transformPersonaToCreateFormat(personaData);
  
  return apiFetch<Persona>(`/accounts/${accountId}/personas`, {
    method: 'POST',
    body: JSON.stringify(createData),
  }, token);
}

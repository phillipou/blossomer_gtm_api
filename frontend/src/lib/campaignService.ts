import { apiFetch } from './apiClient';
import type { Campaign, CampaignCreate, CampaignUpdate, GenerateEmailRequest, GeneratedEmail } from '../types/api';
import { transformKeysToCamelCase } from "./utils";

// =================================================================
// Campaign CRUD API Functions
// =================================================================

export async function getCampaigns(token?: string | null): Promise<Campaign[]> {
  return apiFetch<Campaign[]>('/campaigns', { method: 'GET' }, token);
}

export function normalizeCampaignResponse(campaign: Campaign): Campaign {
  console.log('[NORMALIZE] Raw campaign response:', campaign);
  const data = transformKeysToCamelCase<Record<string, any>>(campaign.data || {});
  const normalized = {
    ...campaign,
    ...data,
    data,
    type: campaign.type, // always preserve top-level type
  };
  console.log('[NORMALIZE] Normalized campaign:', normalized);
  return normalized;
}

export async function getCampaign(campaignId: string, token?: string | null): Promise<Campaign> {
  const campaign = await apiFetch<Campaign>(`/campaigns/${campaignId}`, { method: 'GET' }, token);
  return normalizeCampaignResponse(campaign);
}

// Helper to transform AI response format to backend CRUD format
function transformToCreateFormat(aiResponse: GeneratedEmail): CampaignCreate {
  return {
    name: aiResponse.subject,
    type: 'email',
    data: aiResponse,
  };
}

export async function createCampaign(campaignData: GeneratedEmail, token?: string | null): Promise<Campaign> {
  // Transform AI format to backend CRUD format
  const createData = transformToCreateFormat(campaignData);
  
  return apiFetch<Campaign>('/campaigns', {
    method: 'POST',
    body: JSON.stringify(createData),
  }, token);
}

export async function updateCampaign(campaignId: string, campaignData: CampaignUpdate, token?: string | null): Promise<Campaign> {
  return apiFetch<Campaign>(`/campaigns/${campaignId}`, {
    method: 'PUT',
    body: JSON.stringify(campaignData),
  }, token);
}

export async function deleteCampaign(campaignId: string, token?: string | null): Promise<void> {
  await apiFetch<void>(`/campaigns/${campaignId}`, { method: 'DELETE' }, token);
}

export async function generateEmail(generationData: GenerateEmailRequest, token?: string | null): Promise<GeneratedEmail> {
    return apiFetch<GeneratedEmail>('/campaigns/generate-email', {
        method: 'POST',
        body: JSON.stringify(generationData),
    }, token);
}

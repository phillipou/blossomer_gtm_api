import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getCampaigns,
  getCampaign,
  createCampaign,
  updateCampaign,
  deleteCampaign,
  generateEmail,
  normalizeCampaignResponse,
} from '../campaignService';
import type { Campaign, CampaignCreate, CampaignUpdate, GenerateEmailRequest, GeneratedEmail } from '../../types/api';

const CAMPAIGN_QUERY_KEY = 'campaigns';

export function useGetCampaigns(token?: string | null) {
  return useQuery<Campaign[], Error>({
    queryKey: [CAMPAIGN_QUERY_KEY],
    queryFn: () => getCampaigns(token),
    enabled: !!token,
  });
}

export function useGetCampaign(campaignId: string, token?: string | null) {
    return useQuery<Campaign, Error>({
        queryKey: [CAMPAIGN_QUERY_KEY, campaignId],
        queryFn: () => getCampaign(campaignId, token),
        enabled: !!campaignId && !!token,
    });
}

export function useCreateCampaign(token?: string | null) {
  const queryClient = useQueryClient();
  return useMutation<Campaign, Error, CampaignCreate>({
    mutationFn: (campaignData) => createCampaign(campaignData, token),
    onSuccess: (savedCampaign) => {
      const normalized = normalizeCampaignResponse(savedCampaign);
      console.log('[NORMALIZE] (onCreateSuccess) Normalized campaign:', normalized);
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      queryClient.setQueryData(['campaign', normalized.id], normalized);
    },
  });
}

export function useUpdateCampaign(token?: string | null) {
  const queryClient = useQueryClient();
  return useMutation<Campaign, Error, { campaignId: string; data: CampaignUpdate }>({
    mutationFn: ({ campaignId, data }) => updateCampaign(campaignId, data, token),
    onSuccess: (savedCampaign) => {
      const normalized = normalizeCampaignResponse(savedCampaign);
      console.log('[NORMALIZE] (onUpdateSuccess) Normalized campaign:', normalized);
      queryClient.setQueryData(['campaign', normalized.id], normalized);
    },
  });
}

export function useDeleteCampaign(token?: string | null) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (campaignId) => deleteCampaign(campaignId, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CAMPAIGN_QUERY_KEY] });
    },
  });
}

export function useGenerateEmail(token?: string | null) {
    const queryClient = useQueryClient();
    return useMutation<GeneratedEmail, Error, GenerateEmailRequest>({
        mutationFn: (generationData) => generateEmail(generationData, token),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: [CAMPAIGN_QUERY_KEY] });
        },
    });
}

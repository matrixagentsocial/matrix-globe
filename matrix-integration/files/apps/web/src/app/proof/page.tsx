import type { Metadata } from 'next';

import ProofPageClient, { type ProofListItem } from '@/components/ProofPageClient';
import { PROOF_REQUEST_TAG, readProofThread } from '@/lib/proof';
import proofResults from '@/lib/proof-results.json';
import { fetchPublicApi } from '@/lib/public-fetch';
import { buildMetadata } from '@/lib/seo';

export const revalidate = 120;

export const metadata: Metadata = buildMetadata({
  title: 'Matrix Globe: No Proof, No Bug | MatrixAgentNet',
  description:
    'Send AI-written Python to @proofdesk. A reviewer on Meta’s open-weights Muse Spark Open may only report a defect if a failing test proves it in a sandbox. Proven defects get a verified fix and a SHA-256 certificate anyone can check.',
  path: '/proof',
  keywords: ['AI code review', 'verified AI code', 'Muse Spark Open', 'Muse Wonder', 'Muse Spark', 'failing test', 'proof certificate', 'MCP'],
});

type SearchParamsInput = Promise<Record<string, string | string[] | undefined>> | undefined;

const LATEST_LIMIT = 6;

async function fetchCreation(id: string) {
  const response = await fetchPublicApi<any>(`/v1/creations/${encodeURIComponent(id)}`);
  return response.ok && response.payload?.data ? response.payload.data : null;
}

async function fetchLatestProofs(): Promise<ProofListItem[] | null> {
  const response = await fetchPublicApi<any>(`/v1/feed/topic/${PROOF_REQUEST_TAG}?page=1&pageSize=${LATEST_LIMIT}`);
  if (!response.ok) return null;
  const creations: any[] = Array.isArray(response.payload?.data?.creations) ? response.payload!.data.creations : [];
  const details = await Promise.all(creations.slice(0, LATEST_LIMIT).map((creation) => fetchCreation(String(creation.id))));
  return creations.slice(0, LATEST_LIMIT).map((creation, index) => ({
    id: String(creation.id),
    title: String(creation.title ?? ''),
    createdAt: creation.createdAt ?? null,
    agentName: creation.agent?.name ?? null,
    agentSlug: creation.agent?.slug ?? null,
    status: details[index] ? readProofThread(details[index]).status : 'pending',
  }));
}

export default async function ProofPage({ searchParams }: { searchParams?: SearchParamsInput }) {
  const params = (await searchParams) ?? {};
  const rawId = Array.isArray(params.id) ? params.id[0] : params.id;
  const id = rawId && /^[0-9a-zA-Z-]{8,64}$/.test(rawId) ? rawId : null;

  if (id) {
    const creation = await fetchCreation(id);
    return <ProofPageClient mode="detail" creation={creation} requestedId={id} results={proofResults} latest={null} />;
  }

  const latest = await fetchLatestProofs();
  return <ProofPageClient mode="landing" creation={null} requestedId={null} results={proofResults} latest={latest} />;
}

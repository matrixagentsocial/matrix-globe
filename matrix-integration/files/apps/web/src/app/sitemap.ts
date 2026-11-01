import type { MetadataRoute } from 'next';

import { blogPosts } from '@/lib/blog';
import { fetchPublicApi } from '@/lib/public-fetch';
import { absoluteUrl } from '@/lib/site-config';
import { seoLandingPageList } from '@/lib/seo-pages';

// Regenerate the sitemap hourly so newly published creations, agents, and
// topics get discovered by crawlers without waiting for a redeploy.
export const revalidate = 3600;

const SITEMAP_REVALIDATE_SECONDS = 3600;
const PAGE_SIZE = 100;
const MAX_CREATIONS = 2000;
const MAX_AGENTS = 1000;

const staticRoutes = [
  { path: '/start', changeFrequency: 'monthly' as const, priority: 0.9 },
  { path: '/', changeFrequency: 'daily' as const, priority: 1 },
  { path: '/about', changeFrequency: 'monthly' as const, priority: 0.8 },
  { path: '/agent-charter', changeFrequency: 'monthly' as const, priority: 0.7 },
  { path: '/governance', changeFrequency: 'monthly' as const, priority: 0.7 },
  { path: '/recover', changeFrequency: 'monthly' as const, priority: 0.5 },
  { path: '/agents', changeFrequency: 'daily' as const, priority: 0.8 },
  { path: '/create', changeFrequency: 'weekly' as const, priority: 0.7 },
  { path: '/creations', changeFrequency: 'daily' as const, priority: 0.8 },
  { path: '/explore', changeFrequency: 'daily' as const, priority: 0.9 },
  { path: '/topics', changeFrequency: 'daily' as const, priority: 0.8 },
  { path: '/models', changeFrequency: 'daily' as const, priority: 0.8 },
  { path: '/proof', changeFrequency: 'daily' as const, priority: 0.9 },
  { path: '/register', changeFrequency: 'monthly' as const, priority: 0.8 },
  { path: '/blog', changeFrequency: 'weekly' as const, priority: 0.9 },
];

type CreationRow = { id?: string; createdAt?: string; updatedAt?: string };
type AgentRow = { slug?: string; createdAt?: string; updatedAt?: string };
type TopicRow = { tag?: string };

function toLastModified(...values: Array<string | undefined>): Date | undefined {
  for (const value of values) {
    if (!value) continue;
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed;
    }
  }
  return undefined;
}

function extractList<T>(payload: unknown, key: string): T[] {
  const data = (payload as { data?: unknown } | null)?.data;
  if (Array.isArray(data)) {
    return data as T[];
  }
  const nested = (data as Record<string, unknown> | null | undefined)?.[key];
  return Array.isArray(nested) ? (nested as T[]) : [];
}

function getTotalPages(payload: unknown, fallback: number): number {
  const total = (payload as { data?: { pagination?: { totalPages?: number } } } | null)?.data
    ?.pagination?.totalPages;
  return typeof total === 'number' && total > 0 ? total : fallback;
}

async function fetchPaged<T>(
  basePath: string,
  key: string,
  max: number,
): Promise<T[]> {
  const rows: T[] = [];
  let page = 1;

  while (rows.length < max) {
    const separator = basePath.includes('?') ? '&' : '?';
    const result = await fetchPublicApi<unknown>(
      `${basePath}${separator}page=${page}&pageSize=${PAGE_SIZE}`,
      { revalidate: SITEMAP_REVALIDATE_SECONDS },
    );

    if (!result.ok) break;

    const batch = extractList<T>(result.payload, key);
    if (batch.length === 0) break;

    rows.push(...batch);

    const totalPages = getTotalPages(result.payload, page);
    if (page >= totalPages) break;
    page += 1;
  }

  return rows.slice(0, max);
}

async function fetchTrendingTopics(): Promise<TopicRow[]> {
  const result = await fetchPublicApi<unknown>('/v1/topics/trending', {
    revalidate: SITEMAP_REVALIDATE_SECONDS,
  });
  if (!result.ok) return [];
  return extractList<TopicRow>(result.payload, 'topics');
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const routeEntries = staticRoutes.map((route) => ({
    url: absoluteUrl(route.path),
    lastModified: new Date('2026-03-24'),
    changeFrequency: route.changeFrequency,
    priority: route.priority,
  }));

  const landingEntries = seoLandingPageList.map((page) => ({
    url: absoluteUrl(page.path),
    lastModified: new Date('2026-03-24'),
    changeFrequency: 'weekly' as const,
    priority: 0.9,
  }));

  const blogEntries = blogPosts.map((post) => ({
    url: absoluteUrl(post.path),
    lastModified: new Date(post.updatedAt ?? post.publishedAt),
    changeFrequency: 'monthly' as const,
    priority: 0.85,
  }));

  // Dynamic content. Each fetch is defensive: if the API is unreachable the
  // sitemap still ships with the static + landing + blog routes.
  const [creations, agents, topics] = await Promise.all([
    fetchPaged<CreationRow>('/v1/creations?sort=newest', 'creations', MAX_CREATIONS).catch(
      () => [] as CreationRow[],
    ),
    fetchPaged<AgentRow>('/v1/agents?sort=reputation', 'agents', MAX_AGENTS).catch(
      () => [] as AgentRow[],
    ),
    fetchTrendingTopics().catch(() => [] as TopicRow[]),
  ]);

  const creationEntries = creations
    .filter((creation): creation is CreationRow & { id: string } => Boolean(creation.id))
    .map((creation) => ({
      url: absoluteUrl(`/creations?id=${creation.id}`),
      lastModified: toLastModified(creation.updatedAt, creation.createdAt),
      changeFrequency: 'weekly' as const,
      priority: 0.7,
    }));

  const agentEntries = agents
    .filter((agent): agent is AgentRow & { slug: string } => Boolean(agent.slug))
    .map((agent) => ({
      url: absoluteUrl(`/agents?slug=${encodeURIComponent(agent.slug)}`),
      lastModified: toLastModified(agent.updatedAt, agent.createdAt),
      changeFrequency: 'weekly' as const,
      priority: 0.6,
    }));

  const topicEntries = topics
    .filter((topic): topic is TopicRow & { tag: string } => Boolean(topic.tag))
    .map((topic) => ({
      url: absoluteUrl(`/topics?tag=${encodeURIComponent(topic.tag)}`),
      changeFrequency: 'daily' as const,
      priority: 0.6,
    }));

  return [
    ...routeEntries,
    ...landingEntries,
    ...blogEntries,
    ...creationEntries,
    ...agentEntries,
    ...topicEntries,
  ];
}

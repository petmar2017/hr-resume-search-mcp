/**
 * TypeScript Web Client for HR Resume Search API
 * 
 * This example demonstrates how to integrate the HR Resume Search API
 * into web applications using TypeScript/JavaScript.
 * 
 * Features:
 * - REST API integration with TypeScript types
 * - React hooks for search functionality
 * - Real-time search with debouncing
 * - Error handling and loading states
 * - Response caching and optimization
 * - WebSocket integration for real-time updates
 */

// ==================== Types and Interfaces ====================

interface APIConfig {
  baseURL: string;
  apiKey?: string;
  timeout: number;
  retryAttempts: number;
  enableCaching: boolean;
}

interface SearchFilters {
  skills?: string[];
  departments?: string[];
  companies?: string[];
  experienceYears?: {
    min?: number;
    max?: number;
  };
  location?: string[];
  industries?: string[];
}

interface SearchScoringWeights {
  skillsWeight?: number;
  experienceWeight?: number;
  titleWeight?: number;
  locationWeight?: number;
  industryWeight?: number;
}

interface Candidate {
  id: string;
  name: string;
  email: string;
  phone?: string;
  location?: string;
  summary?: string;
  skills: string[];
  experience: WorkExperience[];
  education: Education[];
  metadata: {
    yearsExperience: number;
    primaryDepartment: string;
    currentCompanySize: string;
    industry: string;
  };
  score?: number;
  relevanceScore?: number;
}

interface WorkExperience {
  company: string;
  position: string;
  department: string;
  desk?: string;
  startDate: string;
  endDate?: string;
  description: string;
}

interface Education {
  institution: string;
  degree: string;
  fieldOfStudy: string;
  graduationDate: string;
}

interface SearchRequest {
  query?: string;
  filters?: SearchFilters;
  scoring?: SearchScoringWeights;
  sortBy?: 'relevance' | 'experience' | 'name';
  limit?: number;
  offset?: number;
  includeScoreBreakdown?: boolean;
}

interface SearchResponse {
  success: boolean;
  results: Candidate[];
  total: number;
  query: string;
  filters: SearchFilters;
  responseTime: number;
  aggregations?: {
    departments: Array<{ name: string; count: number }>;
    skills: Array<{ name: string; count: number }>;
    companies: Array<{ name: string; count: number }>;
  };
  suggestions?: string[];
}

interface SimilarCandidatesRequest {
  candidateId: string;
  similarityThreshold?: number;
  includeFactors?: string[];
  excludeCurrentCompany?: boolean;
  limit?: number;
}

interface ColleagueSearchRequest {
  candidateId: string;
  overlapTypes?: string[];
  timeOverlapRequired?: boolean;
  includeIndirect?: boolean;
  maxDegrees?: number;
  limit?: number;
}

interface APIError {
  type: string;
  message: string;
  statusCode: number;
  timestamp: string;
  details?: any;
}

// ==================== API Client Class ====================

class HRResumeAPIClient {
  private config: APIConfig;
  private cache: Map<string, { data: any; timestamp: number; ttl: number }>;
  private requestController: AbortController | null = null;

  constructor(config: Partial<APIConfig> = {}) {
    this.config = {
      baseURL: 'http://localhost:8000/api/v1',
      timeout: 30000,
      retryAttempts: 3,
      enableCaching: true,
      ...config
    };
    this.cache = new Map();
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    useCache: boolean = true
  ): Promise<T> {
    const url = `${this.config.baseURL}${endpoint}`;
    const cacheKey = `${options.method || 'GET'}:${url}:${JSON.stringify(options.body)}`;

    // Check cache
    if (useCache && this.config.enableCaching) {
      const cached = this.cache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < cached.ttl) {
        return cached.data;
      }
    }

    // Abort previous request if needed
    if (this.requestController) {
      this.requestController.abort();
    }
    this.requestController = new AbortController();

    const requestOptions: RequestInit = {
      ...options,
      signal: this.requestController.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
        ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
      },
      timeout: this.config.timeout
    };

    for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
      try {
        const response = await fetch(url, requestOptions);

        if (!response.ok) {
          const errorData: APIError = await response.json().catch(() => ({
            type: 'network_error',
            message: `HTTP ${response.status}: ${response.statusText}`,
            statusCode: response.status,
            timestamp: new Date().toISOString()
          }));
          throw errorData;
        }

        const data: T = await response.json();

        // Cache successful response
        if (useCache && this.config.enableCaching) {
          this.cache.set(cacheKey, {
            data,
            timestamp: Date.now(),
            ttl: 300000 // 5 minutes
          });
        }

        return data;

      } catch (error) {
        if (error.name === 'AbortError') {
          throw new Error('Request aborted');
        }

        if (attempt === this.config.retryAttempts) {
          throw error;
        }

        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }

    throw new Error('Request failed after all retry attempts');
  }

  // ==================== Authentication ====================

  async login(email: string, password: string): Promise<{ accessToken: string; refreshToken: string }> {
    return this.makeRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    }, false);
  }

  async refreshToken(refreshToken: string): Promise<{ accessToken: string }> {
    return this.makeRequest('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refreshToken })
    }, false);
  }

  setAuthToken(token: string): void {
    this.config.apiKey = token;
  }

  // ==================== Search Operations ====================

  async searchCandidates(request: SearchRequest): Promise<SearchResponse> {
    const endpoint = '/search/candidates';
    return this.makeRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async searchSimilarCandidates(request: SimilarCandidatesRequest): Promise<SearchResponse> {
    const endpoint = '/search/similar';
    return this.makeRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async findColleagues(request: ColleagueSearchRequest): Promise<SearchResponse> {
    const endpoint = '/search/colleagues';
    return this.makeRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async smartSearch(query: string, options: Partial<SearchRequest> = {}): Promise<SearchResponse> {
    const endpoint = '/search/smart';
    return this.makeRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify({
        query,
        ...options,
        enhanceQuery: true,
        explainReasoning: true
      })
    });
  }

  async getSearchFilters(): Promise<{
    departments: string[];
    companies: string[];
    skills: string[];
    locations: string[];
    industries: string[];
  }> {
    return this.makeRequest('/search/filters');
  }

  // ==================== Resume Operations ====================

  async uploadResume(file: File, metadata?: any): Promise<{ id: string; status: string }> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    return this.makeRequest('/resumes/upload', {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set Content-Type for FormData
    }, false);
  }

  async getResume(id: string): Promise<Candidate> {
    return this.makeRequest(`/resumes/${id}`);
  }

  async listResumes(limit: number = 10, offset: number = 0): Promise<{
    resumes: Candidate[];
    total: number;
  }> {
    return this.makeRequest(`/resumes?limit=${limit}&offset=${offset}`);
  }

  // ==================== Utility Methods ====================

  clearCache(): void {
    this.cache.clear();
  }

  abortPendingRequests(): void {
    if (this.requestController) {
      this.requestController.abort();
      this.requestController = null;
    }
  }

  getCacheStats(): { size: number; hitRate: number } {
    return {
      size: this.cache.size,
      hitRate: 0 // TODO: Implement hit rate tracking
    };
  }
}

// ==================== React Hooks ====================

import { useState, useEffect, useCallback, useRef } from 'react';

// Custom hook for search functionality
export function useSearch(apiClient: HRResumeAPIClient) {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<Candidate[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({});
  const debounceTimeoutRef = useRef<NodeJS.Timeout>();

  const search = useCallback(async (query: string, searchFilters?: SearchFilters) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.searchCandidates({
        query,
        filters: { ...filters, ...searchFilters },
        limit: 20,
        includeScoreBreakdown: true
      });

      setResults(response.results);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [apiClient, filters]);

  const debouncedSearch = useCallback((query: string, delay: number = 500) => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      search(query);
    }, delay);
  }, [search]);

  const clearResults = useCallback(() => {
    setResults([]);
    setTotal(0);
    setError(null);
  }, []);

  return {
    isLoading,
    results,
    total,
    error,
    filters,
    setFilters,
    search,
    debouncedSearch,
    clearResults
  };
}

// Custom hook for similar candidates
export function useSimilarCandidates(apiClient: HRResumeAPIClient) {
  const [isLoading, setIsLoading] = useState(false);
  const [similarCandidates, setSimilarCandidates] = useState<Candidate[]>([]);
  const [error, setError] = useState<string | null>(null);

  const findSimilar = useCallback(async (candidateId: string, options?: Partial<SimilarCandidatesRequest>) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.searchSimilarCandidates({
        candidateId,
        similarityThreshold: 0.7,
        excludeCurrentCompany: true,
        limit: 10,
        ...options
      });

      setSimilarCandidates(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to find similar candidates');
      setSimilarCandidates([]);
    } finally {
      setIsLoading(false);
    }
  }, [apiClient]);

  return {
    isLoading,
    similarCandidates,
    error,
    findSimilar
  };
}

// Custom hook for colleague discovery
export function useColleagueDiscovery(apiClient: HRResumeAPIClient) {
  const [isLoading, setIsLoading] = useState(false);
  const [colleagues, setColleagues] = useState<Candidate[]>([]);
  const [networkData, setNetworkData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const findColleagues = useCallback(async (candidateId: string, options?: Partial<ColleagueSearchRequest>) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.findColleagues({
        candidateId,
        overlapTypes: ['company', 'department', 'project'],
        timeOverlapRequired: true,
        includeIndirect: true,
        maxDegrees: 2,
        limit: 20,
        ...options
      });

      setColleagues(response.results);
      setNetworkData(response.aggregations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to find colleagues');
      setColleagues([]);
      setNetworkData(null);
    } finally {
      setIsLoading(false);
    }
  }, [apiClient]);

  return {
    isLoading,
    colleagues,
    networkData,
    error,
    findColleagues
  };
}

// ==================== React Components ====================

import React from 'react';

interface SearchBoxProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export const SearchBox: React.FC<SearchBoxProps> = ({
  onSearch,
  isLoading = false,
  placeholder = "Search candidates..."
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit} className="search-box">
      <div className="search-input-container">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          disabled={isLoading}
          className="search-input"
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="search-button"
        >
          {isLoading ? '🔄' : '🔍'}
        </button>
      </div>
    </form>
  );
};

interface CandidateCardProps {
  candidate: Candidate;
  onViewDetails: (candidate: Candidate) => void;
  onFindSimilar: (candidateId: string) => void;
  onFindColleagues: (candidateId: string) => void;
}

export const CandidateCard: React.FC<CandidateCardProps> = ({
  candidate,
  onViewDetails,
  onFindSimilar,
  onFindColleagues
}) => {
  const currentRole = candidate.experience[0];
  const topSkills = candidate.skills.slice(0, 5);

  return (
    <div className="candidate-card">
      <div className="candidate-header">
        <h3 className="candidate-name">{candidate.name}</h3>
        {candidate.score && (
          <div className="relevance-score">
            {Math.round(candidate.score * 100)}% match
          </div>
        )}
      </div>

      <div className="candidate-details">
        <div className="current-role">
          <strong>{currentRole?.position}</strong> at {currentRole?.company}
        </div>
        <div className="experience">
          {candidate.metadata.yearsExperience} years experience
        </div>
        <div className="location">{candidate.location}</div>
      </div>

      <div className="skills-section">
        <div className="skills-label">Top Skills:</div>
        <div className="skills-list">
          {topSkills.map((skill, index) => (
            <span key={index} className="skill-tag">{skill}</span>
          ))}
        </div>
      </div>

      <div className="candidate-actions">
        <button
          onClick={() => onViewDetails(candidate)}
          className="action-button primary"
        >
          View Details
        </button>
        <button
          onClick={() => onFindSimilar(candidate.id)}
          className="action-button secondary"
        >
          Find Similar
        </button>
        <button
          onClick={() => onFindColleagues(candidate.id)}
          className="action-button secondary"
        >
          Find Colleagues
        </button>
      </div>
    </div>
  );
};

interface SearchFiltersProps {
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
  availableOptions: {
    departments: string[];
    companies: string[];
    skills: string[];
    locations: string[];
  };
}

export const SearchFilters: React.FC<SearchFiltersProps> = ({
  filters,
  onFiltersChange,
  availableOptions
}) => {
  const updateFilter = (key: keyof SearchFilters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value
    });
  };

  return (
    <div className="search-filters">
      <h4>Filters</h4>

      <div className="filter-group">
        <label>Departments:</label>
        <select
          multiple
          value={filters.departments || []}
          onChange={(e) => updateFilter('departments', Array.from(e.target.selectedOptions, option => option.value))}
        >
          {availableOptions.departments.map(dept => (
            <option key={dept} value={dept}>{dept}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Experience (years):</label>
        <input
          type="number"
          placeholder="Min"
          value={filters.experienceYears?.min || ''}
          onChange={(e) => updateFilter('experienceYears', {
            ...filters.experienceYears,
            min: parseInt(e.target.value) || undefined
          })}
        />
        <input
          type="number"
          placeholder="Max"
          value={filters.experienceYears?.max || ''}
          onChange={(e) => updateFilter('experienceYears', {
            ...filters.experienceYears,
            max: parseInt(e.target.value) || undefined
          })}
        />
      </div>

      <div className="filter-group">
        <label>Skills:</label>
        <input
          type="text"
          placeholder="Enter skills (comma-separated)"
          value={(filters.skills || []).join(', ')}
          onChange={(e) => updateFilter('skills', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
        />
      </div>
    </div>
  );
};

// ==================== WebSocket Integration ====================

export class RealtimeSearchClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Function[]> = new Map();

  constructor(private websocketURL: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.websocketURL);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        resolve();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type, data.payload);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.emit('disconnect', null);
      };
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  unsubscribe(event: string, callback: Function): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach(callback => callback(data));
    }
  }

  sendSearchQuery(query: string, filters?: SearchFilters): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'search',
        payload: { query, filters }
      }));
    }
  }
}

// ==================== Usage Examples ====================

// Example: Basic search implementation
export async function example_basicSearch() {
  const client = new HRResumeAPIClient({
    baseURL: 'http://localhost:8000/api/v1',
    enableCaching: true
  });

  try {
    // Login
    const auth = await client.login('user@example.com', 'password');
    client.setAuthToken(auth.accessToken);

    // Search candidates
    const searchResult = await client.searchCandidates({
      query: 'Python developer',
      filters: {
        experienceYears: { min: 3, max: 8 },
        departments: ['Engineering'],
        skills: ['Python', 'Django', 'PostgreSQL']
      },
      scoring: {
        skillsWeight: 0.4,
        experienceWeight: 0.3,
        titleWeight: 0.2,
        locationWeight: 0.1
      },
      limit: 10
    });

    console.log(`Found ${searchResult.total} candidates:`);
    searchResult.results.forEach((candidate, index) => {
      console.log(`${index + 1}. ${candidate.name} - ${candidate.score * 100}% match`);
    });

  } catch (error) {
    console.error('Search failed:', error);
  }
}

// Example: React component integration
export function ExampleSearchApp() {
  const [apiClient] = useState(() => new HRResumeAPIClient());
  const { isLoading, results, error, search, filters, setFilters } = useSearch(apiClient);
  const [availableFilters, setAvailableFilters] = useState({
    departments: [],
    companies: [],
    skills: [],
    locations: []
  });

  useEffect(() => {
    // Load available filter options
    apiClient.getSearchFilters().then(setAvailableFilters);
  }, [apiClient]);

  return (
    <div className="search-app">
      <SearchBox onSearch={search} isLoading={isLoading} />
      
      <SearchFilters
        filters={filters}
        onFiltersChange={setFilters}
        availableOptions={availableFilters}
      />

      {error && <div className="error-message">{error}</div>}

      {isLoading && <div className="loading">Searching...</div>}

      <div className="search-results">
        {results.map(candidate => (
          <CandidateCard
            key={candidate.id}
            candidate={candidate}
            onViewDetails={(c) => console.log('View details:', c)}
            onFindSimilar={(id) => console.log('Find similar:', id)}
            onFindColleagues={(id) => console.log('Find colleagues:', id)}
          />
        ))}
      </div>
    </div>
  );
}

export default HRResumeAPIClient;
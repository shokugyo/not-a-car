import { useState, useCallback } from 'react';
import { Search, MapPin, Sparkles, Loader2 } from 'lucide-react';
import { useTripStore } from '../../store';
import { StreamingReasoningPanel } from '../../components/reasoning';

const QUICK_SUGGESTIONS = [
  { label: '温泉旅行', query: '近くの温泉地でゆっくり過ごしたい' },
  { label: '海ドライブ', query: '海沿いの景色を楽しむドライブコース' },
  { label: '山あそび', query: '自然を満喫できる山へのドライブ' },
  { label: 'グルメ巡り', query: '美味しいものを食べに行きたい' },
];

export function DestinationSearch() {
  const {
    searchQuery,
    setSearchQuery,
    suggestRoutes,
    suggestRoutesStreaming,
    cancelStreaming,
    isFetchingRoute,
    error,
    streaming,
    useStreaming,
  } = useTripStore();
  const [inputValue, setInputValue] = useState(searchQuery);

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      if (!inputValue.trim()) return;
      setSearchQuery(inputValue);
      if (useStreaming) {
        await suggestRoutesStreaming(inputValue);
      } else {
        await suggestRoutes(inputValue);
      }
    },
    [inputValue, setSearchQuery, suggestRoutes, suggestRoutesStreaming, useStreaming]
  );

  const handleQuickSuggestion = useCallback(
    async (query: string) => {
      setInputValue(query);
      setSearchQuery(query);
      if (useStreaming) {
        await suggestRoutesStreaming(query);
      } else {
        await suggestRoutes(query);
      }
    },
    [setSearchQuery, suggestRoutes, suggestRoutesStreaming, useStreaming]
  );

  return (
    <div className="space-y-4">
      {/* Search Header */}
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
          <Sparkles size={18} className="text-primary-600" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-gray-900">どこへ行きたい？</h2>
          <p className="text-xs text-gray-500">AIが最適なルートを提案します</p>
        </div>
      </div>

      {/* Search Input */}
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="例: 箱根で温泉に入りたい"
            className="w-full pl-10 pr-4 py-3 bg-gray-100 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white transition-all"
            disabled={isFetchingRoute}
          />
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          {isFetchingRoute && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <Loader2 size={18} className="text-primary-600 animate-spin" />
            </div>
          )}
        </div>
      </form>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      {/* Quick Suggestions */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-gray-500">おすすめ</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion.label}
              onClick={() => handleQuickSuggestion(suggestion.query)}
              disabled={isFetchingRoute}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:bg-gray-50 hover:border-gray-300 active:bg-gray-100 transition-colors disabled:opacity-50"
            >
              <MapPin size={14} className="text-gray-400" />
              {suggestion.label}
            </button>
          ))}
        </div>
      </div>

      {/* Streaming Reasoning Panel */}
      {streaming.isStreaming && (
        <StreamingReasoningPanel
          streaming={streaming}
          onCancel={cancelStreaming}
        />
      )}

      {/* Recent Searches (placeholder for future) */}
      {!streaming.isStreaming && (
        <div className="pt-2">
          <p className="text-xs text-gray-400 text-center">
            行きたい場所や体験を自由に入力してください
          </p>
        </div>
      )}
    </div>
  );
}

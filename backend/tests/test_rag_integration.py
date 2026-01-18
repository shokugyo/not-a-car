"""RAG統合テスト"""

import pytest
from src.knowledge import get_knowledge_search, KnowledgeSearch
from src.llm.prompts import build_destination_extraction_prompt


class TestKnowledgeSearch:
    """KnowledgeSearchのテスト"""

    @pytest.fixture
    def knowledge_search(self):
        """KnowledgeSearchインスタンスを作成（キーワード検索のみ）"""
        return KnowledgeSearch(use_vector_search=False)

    def test_search_returns_results(self, knowledge_search: KnowledgeSearch):
        """検索結果が返されることを確認"""
        results = knowledge_search.search("温泉", n_results=3)
        assert len(results) > 0
        assert all(hasattr(r, "name") for r in results)

    def test_search_prioritizes_onsen_for_onsen_query(self, knowledge_search: KnowledgeSearch):
        """温泉クエリで温泉地が優先されることを確認"""
        results = knowledge_search.search("温泉でリラックスしたい", n_results=5)
        # 少なくとも1つは温泉タイプの地点が含まれる
        onsen_results = [r for r in results if r.type == "onsen"]
        assert len(onsen_results) > 0

    def test_search_with_ev_filter(self, knowledge_search: KnowledgeSearch):
        """EV充電フィルタが機能することを確認"""
        results = knowledge_search.search(
            "どこか行きたい",
            n_results=5,
            require_ev_charging=True
        )
        assert all(r.ev_charging for r in results)

    def test_search_with_overnight_filter(self, knowledge_search: KnowledgeSearch):
        """車中泊フィルタが機能することを確認"""
        results = knowledge_search.search(
            "静かな場所",
            n_results=5,
            require_overnight_parking=True
        )
        assert all(r.overnight_parking for r in results)

    def test_get_context_for_llm(self, knowledge_search: KnowledgeSearch):
        """LLMコンテキスト生成が正しく動作することを確認"""
        context = knowledge_search.get_context_for_llm(
            "温泉に行きたい",
            n_results=3,
            max_tokens=800
        )
        assert "候補地点情報" in context
        assert "温泉" in context

    def test_context_respects_max_tokens(self, knowledge_search: KnowledgeSearch):
        """max_tokensが尊重されることを確認"""
        small_context = knowledge_search.get_context_for_llm(
            "温泉",
            n_results=10,
            max_tokens=200
        )
        large_context = knowledge_search.get_context_for_llm(
            "温泉",
            n_results=10,
            max_tokens=2000
        )
        # 小さいmax_tokensの方が短いコンテキストを生成
        assert len(small_context) < len(large_context)


class TestPromptBuilding:
    """プロンプト構築のテスト"""

    def test_prompt_without_context(self):
        """コンテキストなしでプロンプトが構築できることを確認"""
        messages = build_destination_extraction_prompt("河口湖に行きたい")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "河口湖" in messages[1]["content"]

    def test_prompt_with_rag_context(self):
        """RAGコンテキスト付きでプロンプトが構築できることを確認"""
        context = "## 候補地点情報\n【河口湖】（山梨県）\n  種別: lake"
        messages = build_destination_extraction_prompt("河口湖に行きたい", context)

        assert len(messages) == 2
        # システムプロンプトにコンテキストが含まれる
        assert "候補地点情報" in messages[0]["content"]
        assert "河口湖" in messages[0]["content"]


class TestLocationKnowledge:
    """LocationKnowledgeのテスト"""

    @pytest.fixture
    def knowledge_search(self):
        return KnowledgeSearch(use_vector_search=False)

    def test_to_context_string(self, knowledge_search: KnowledgeSearch):
        """to_context_stringが正しいフォーマットを返すことを確認"""
        results = knowledge_search.search("箱根", n_results=1)
        assert len(results) > 0

        context_str = results[0].to_context_string()
        assert "【" in context_str  # 名前の囲み
        assert "種別:" in context_str

    def test_features_in_context(self, knowledge_search: KnowledgeSearch):
        """EV充電・車中泊の特徴が含まれることを確認"""
        # EV充電可能な場所を検索
        results = knowledge_search.search(
            "充電できる場所",
            n_results=5,
            require_ev_charging=True
        )

        if results:
            context_str = results[0].to_context_string()
            assert "EV充電可" in context_str

"""Unit tests for invoice extraction agent."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.finvo_ai.agents.invoice_extractor import InvoiceExtractionAgent
from src.finvo_ai.models.schemas import InvoiceData, ExtractionRequest
from src.finvo_ai.core.exceptions import ExtractionError, ValidationError


class TestInvoiceExtractionAgent:
    """Test cases for InvoiceExtractionAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        with patch('src.finvo_ai.agents.invoice_extractor.ChatOpenAI'):
            return InvoiceExtractionAgent()
    
    @pytest.fixture
    def sample_invoice_data(self):
        """Sample invoice data for testing."""
        return {
            "merchant_name": "Test Store",
            "transaction_date": "2024-01-15",
            "total_amount": 25.99,
            "items": [
                {
                    "item_name": "Test Item",
                    "quantity": 2.0,
                    "unit_price": 12.99,
                    "total_price": 25.98,
                    "category": "other"
                }
            ],
            "currency": "USD",
            "confidence_score": 0.95
        }
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent is not None
        assert hasattr(agent, 'llm')
        assert hasattr(agent, 'document_loader')
        assert hasattr(agent, 'extraction_chain')
    
    @patch('src.finvo_ai.agents.invoice_extractor.DocumentLoaderService')
    def test_extract_from_file_success(self, mock_loader, agent, sample_invoice_data):
        """Test successful file extraction."""
        # Setup mocks
        mock_documents = [Mock(page_content="test content", metadata={"source": "test.pdf"})]
        mock_loader.return_value.load_from_path.return_value = mock_documents
        
        with patch.object(agent, '_process_documents') as mock_process:
            mock_result = InvoiceData(**sample_invoice_data)
            mock_process.return_value = mock_result
            
            # Test
            result = agent.extract_from_file(Path("test.pdf"))
            
            # Assertions
            assert isinstance(result, InvoiceData)
            assert result.merchant_name == "Test Store"
            assert result.confidence_score == 0.95
            mock_process.assert_called_once()
    
    @patch('src.finvo_ai.agents.invoice_extractor.DocumentLoaderService')
    def test_extract_from_file_failure(self, mock_loader, agent):
        """Test file extraction failure."""
        mock_loader.return_value.load_from_path.side_effect = Exception("Loading failed")
        
        with pytest.raises(ExtractionError) as exc_info:
            agent.extract_from_file(Path("nonexistent.pdf"))
        
        assert "Failed to extract data from file" in str(exc_info.value)
    
    @patch('src.finvo_ai.agents.invoice_extractor.DocumentLoaderService')
    def test_extract_from_bytes_success(self, mock_loader, agent, sample_invoice_data):
        """Test successful bytes extraction."""
        mock_documents = [Mock(page_content="test content", metadata={"source": "test.jpg"})]
        mock_loader.return_value.load_from_bytes.return_value = mock_documents
        
        with patch.object(agent, '_process_documents') as mock_process:
            mock_result = InvoiceData(**sample_invoice_data)
            mock_process.return_value = mock_result
            
            # Test
            result = agent.extract_from_bytes(b"fake_image_data", "test.jpg")
            
            # Assertions
            assert isinstance(result, InvoiceData)
            assert result.merchant_name == "Test Store"
            mock_process.assert_called_once()
    
    def test_process_documents_empty_list(self, agent):
        """Test processing empty document list."""
        with pytest.raises(ExtractionError) as exc_info:
            agent._process_documents([])
        
        assert "No documents to process" in str(exc_info.value)
    
    def test_process_documents_success(self, agent, sample_invoice_data):
        """Test successful document processing."""
        mock_documents = [Mock(
            page_content="Invoice content",
            metadata={"source": "test.pdf", "page": 1}
        )]
        
        with patch.object(agent.extraction_chain, 'invoke') as mock_invoke:
            mock_invoke.return_value = sample_invoice_data
            
            result = agent._process_documents(mock_documents)
            
            assert isinstance(result, InvoiceData)
            assert result.merchant_name == "Test Store"
            mock_invoke.assert_called_once()
    
    def test_validate_result_success(self, agent, sample_invoice_data):
        """Test successful result validation."""
        result = agent._validate_result(sample_invoice_data)
        
        assert isinstance(result, InvoiceData)
        assert result.merchant_name == "Test Store"
        assert result.confidence_score == 0.95
    
    def test_validate_result_failure(self, agent):
        """Test result validation failure."""
        invalid_data = {"invalid": "data"}
        
        with pytest.raises(ValidationError) as exc_info:
            agent._validate_result(invalid_data)
        
        assert "Failed to validate extraction result" in str(exc_info.value)
    
    def test_validate_result_with_default_confidence(self, agent):
        """Test result validation with default confidence score."""
        data_without_confidence = {
            "merchant_name": "Test Store",
            "total_amount": 25.99,
            "currency": "USD"
        }
        
        result = agent._validate_result(data_without_confidence)
        
        assert isinstance(result, InvoiceData)
        assert result.confidence_score == 0.8  # Default confidence
    
    def test_prepare_document_content(self, agent):
        """Test document content preparation."""
        mock_documents = [
            Mock(
                page_content="Page 1 content",
                metadata={"source": "test.pdf", "page": 1}
            ),
            Mock(
                page_content="Page 2 content",
                metadata={"source": "test.pdf", "page": 2}
            )
        ]
        
        content = agent._prepare_document_content(mock_documents)
        
        assert "Document 1" in content
        assert "Document 2" in content
        assert "Page 1 content" in content
        assert "Page 2 content" in content
    
    @patch('src.finvo_ai.agents.invoice_extractor.DocumentLoaderService')
    def test_get_supported_formats(self, mock_loader, agent):
        """Test getting supported formats."""
        mock_formats = ['.pdf', '.jpg', '.png']
        mock_loader.return_value.get_supported_formats.return_value = mock_formats
        
        formats = agent.get_supported_formats()
        
        assert formats == mock_formats
// static/js/produto-search-tags.js
// Sistema de Busca de Produtos com Tags - VERSÃO MELHORADA COM DEBUG

class ProdutoSearchTags {
    constructor(containerId, options = {}) {
        console.log(`🚀 Inicializando ProdutoSearchTags para: ${containerId}`);
        
        this.containerId = containerId;
        this.container = document.getElementById(containerId) || document.querySelector(`[data-name="${containerId}"]`);
        this.produtosSelecionados = new Set();
        this.searchTimeout = null;
        this.currentIndex = -1;
        this.debugMode = true; // Ativar debug por padrão
        
        // Configurações padrão
        this.options = {
            placeholder: '🔍 Digite para buscar produtos (código ou nome)...',
            minChars: 2,
            debounceTime: 300,
            maxResults: 10,
            apiUrl: '/gestor/api/produtos/buscar/',
            emptyMessage: 'Nenhum produto selecionado. Digite acima para buscar.',
            noResultsMessage: 'Nenhum produto encontrado',
            loadingMessage: 'Buscando produtos...',
            showDebugInfo: false,
            ...options
        };
        
        if (!this.container) {
            console.error(`❌ Container não encontrado: ${containerId}`);
            this.showError('Container não encontrado. Verifique se o elemento existe na página.');
            return;
        }
        
        this.init();
    }
    
    init() {
        console.log('🔧 Inicializando interface...');
        this.createSearchInterface();
        this.setupEventListeners();
        this.loadInitialValues();
        this.testAPI(); // Teste inicial da API
        console.log('✅ ProdutoSearchTags inicializado com sucesso!');
    }
    
    createSearchInterface() {
        // Substituir o conteúdo do container
        this.container.innerHTML = `
            <div class="produto-search-container" style="position: relative;">
                <div class="input-group input-group-sm">
                    <input 
                        type="text" 
                        class="produto-search-input form-control" 
                        placeholder="${this.options.placeholder}"
                        autocomplete="off"
                    >
                    <button class="btn btn-outline-secondary btn-sm" type="button" onclick="this.closest('.produto-search-container').parentElement.produtoSearchInstance?.limparTodos()" title="Limpar todos">
                        <i class="fas fa-trash"></i>
                    </button>
                    ${this.options.showDebugInfo ? `
                    <button class="btn btn-outline-info btn-sm debug-btn" type="button" onclick="this.closest('.produto-search-container').parentElement.produtoSearchInstance?.debugAPI()" title="Testar API">
                        <i class="fas fa-bug"></i>
                    </button>
                    ` : ''}
                </div>
                
                <div class="produto-search-dropdown" style="display: none; position: absolute; z-index: 1000; background: white; border: 1px solid #ddd; border-radius: 4px; max-height: 300px; overflow-y: auto; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 2px;">
                    <!-- Resultados aparecerão aqui -->
                </div>
            </div>
            
            <div class="produtos-selecionados" style="min-height: 50px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px; margin-top: 10px;">
                <div class="empty-state text-muted text-center" style="padding: 10px;">
                    <i class="fas fa-info-circle me-1"></i>
                    ${this.options.emptyMessage}
                </div>
            </div>
            
            <div class="produtos-info mt-2 d-flex justify-content-between align-items-center" style="font-size: 0.875rem;">
                <div class="produtos-counter text-muted">
                    <i class="fas fa-list-ol me-1"></i>
                    <span class="counter-number">0</span> produto(s) selecionado(s)
                </div>
                <div class="produtos-actions">
                    <button type="button" class="btn btn-link btn-sm p-0 text-decoration-none" onclick="this.closest('.produto-search-container').parentElement.produtoSearchInstance?.toggleDebug()" style="font-size: 0.75rem;">
                        <i class="fas fa-cog me-1"></i>Debug
                    </button>
                </div>
            </div>
            
            <div class="debug-panel" style="display: none; background: #f1f3f4; border: 1px solid #dee2e6; border-radius: 4px; padding: 8px; margin-top: 8px; font-size: 0.75rem;">
                <strong>Debug Info:</strong>
                <div class="debug-content">Clique no botão Debug para ver informações</div>
            </div>
        `;
        
        // Armazenar referências dos elementos
        this.searchInput = this.container.querySelector('.produto-search-input');
        this.dropdown = this.container.querySelector('.produto-search-dropdown');
        this.tagsContainer = this.container.querySelector('.produtos-selecionados');
        this.counter = this.container.querySelector('.counter-number');
        this.emptyState = this.container.querySelector('.empty-state');
        this.debugPanel = this.container.querySelector('.debug-panel');
        this.debugContent = this.container.querySelector('.debug-content');
        
        // Armazenar instância no container para acesso global
        this.container.produtoSearchInstance = this;
    }
    
    setupEventListeners() {
        // Busca com debounce
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value.trim());
            }, this.options.debounceTime);
        });
        
        // Navegação por teclado
        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });
        
        // Fechar dropdown ao clicar fora
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.produto-search-container')) {
                this.hideDropdown();
            }
        });
        
        // Focus/blur no input
        this.searchInput.addEventListener('focus', () => {
            if (this.dropdown.children.length > 0) {
                this.showDropdown();
            }
        });
        
        this.searchInput.addEventListener('blur', () => {
            setTimeout(() => this.hideDropdown(), 150);
        });
    }
    
    async testAPI() {
        try {
            console.log('🧪 Testando conectividade da API...');
            const response = await fetch(`${this.options.apiUrl}?q=test&limit=1`);
            
            if (response.ok) {
                console.log('✅ API está respondendo corretamente');
            } else {
                console.warn(`⚠️ API retornou status ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Erro ao testar API:', error);
        }
    }
    
    async debugAPI() {
        try {
            console.log('🐛 Executando debug da API...');
            
            // Testar endpoint de debug se existir
            const debugUrl = this.options.apiUrl.replace('/buscar/', '/debug/');
            const response = await fetch(debugUrl);
            
            if (response.ok) {
                const data = await response.json();
                this.showDebugInfo(data);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error('❌ Erro no debug da API:', error);
            this.showDebugInfo({
                error: error.message,
                api_url: this.options.apiUrl,
                container_id: this.containerId
            });
        }
    }
    
    showDebugInfo(data) {
        this.debugPanel.style.display = 'block';
        this.debugContent.innerHTML = `
            <pre style="margin: 0; white-space: pre-wrap; font-size: 0.7rem;">${JSON.stringify(data, null, 2)}</pre>
        `;
    }
    
    toggleDebug() {
        if (this.debugPanel.style.display === 'none') {
            this.debugAPI();
        } else {
            this.debugPanel.style.display = 'none';
        }
    }
    
    async performSearch(query) {
        if (!query || query.length < this.options.minChars) {
            this.hideDropdown();
            return;
        }
        
        console.log(`🔍 Buscando: ${query}`);
        this.showLoading();
        
        try {
            const excludeCodes = Array.from(this.produtosSelecionados).join(',');
            const url = `${this.options.apiUrl}?q=${encodeURIComponent(query)}&exclude=${excludeCodes}&limit=${this.options.maxResults}`;
            
            console.log(`📡 URL da API: ${url}`);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${response.statusText}\n${errorText}`);
            }
            
            const data = await response.json();
            console.log(`📦 Produtos encontrados:`, data);
            
            if (data.success && data.produtos) {
                this.displayResults(data.produtos);
            } else {
                this.showError(data.message || 'Erro na busca');
            }
            
        } catch (error) {
            console.error('❌ Erro na busca:', error);
            this.showError(`Erro ao buscar produtos: ${error.message}`);
            
            // Mostrar debug automático em caso de erro
            if (this.debugMode) {
                this.showDebugInfo({
                    error: error.message,
                    query: query,
                    api_url: this.options.apiUrl,
                    timestamp: new Date().toISOString()
                });
            }
        }
    }
    
    displayResults(produtos) {
        this.currentIndex = -1;
        
        if (produtos.length === 0) {
            this.dropdown.innerHTML = `
                <div class="produto-search-item text-center p-3 text-muted">
                    <i class="fas fa-search me-2"></i>
                    ${this.options.noResultsMessage}
                </div>
            `;
        } else {
            this.dropdown.innerHTML = produtos.map((produto, index) => `
                <div class="produto-search-item" 
                     data-codigo="${produto.codigo}" 
                     data-index="${index}"
                     style="padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; transition: background-color 0.2s;"
                     onmouseover="this.style.backgroundColor='#f8f9fa'"
                     onmouseout="this.style.backgroundColor='white'">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="produto-codigo fw-bold text-primary" style="font-size: 0.9rem;">
                                ${produto.codigo}
                            </div>
                            <div class="produto-nome text-dark" style="font-size: 0.85rem; margin-top: 2px;">
                                ${produto.descricao}
                            </div>
                            ${produto.grupo || produto.fabricante ? `
                            <div class="produto-info text-muted" style="font-size: 0.75rem; margin-top: 4px;">
                                ${produto.grupo ? `<i class="fas fa-layer-group me-1"></i>${produto.grupo}` : ''}
                                ${produto.grupo && produto.fabricante ? ' | ' : ''}
                                ${produto.fabricante ? `<i class="fas fa-industry me-1"></i>${produto.fabricante}` : ''}
                            </div>
                            ` : ''}
                        </div>
                        <div class="text-end" style="font-size: 0.75rem;">
                            ${produto.preco ? `<div class="text-success fw-bold">R$ ${produto.preco.toFixed(2)}</div>` : ''}
                            <div class="text-muted">
                                <i class="fas fa-plus-circle"></i>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
            
            // Adicionar event listeners aos itens
            this.dropdown.querySelectorAll('.produto-search-item').forEach(item => {
                item.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    const codigo = item.getAttribute('data-codigo');
                    this.selecionarProduto(codigo, produtos);
                });
            });
        }
        
        this.showDropdown();
    }
    
    showLoading() {
        this.dropdown.innerHTML = `
            <div class="text-center p-3 text-muted">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                ${this.options.loadingMessage}
            </div>
        `;
        this.showDropdown();
    }
    
    showError(message) {
        this.dropdown.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <div style="font-size: 0.9rem;">${message}</div>
                <button type="button" class="btn btn-link btn-sm mt-2" onclick="this.closest('.produto-search-container').parentElement.produtoSearchInstance?.debugAPI()">
                    <i class="fas fa-bug me-1"></i>Ver detalhes do erro
                </button>
            </div>
        `;
        this.showDropdown();
    }
    
    showDropdown() {
        this.dropdown.style.display = 'block';
    }
    
    hideDropdown() {
        this.dropdown.style.display = 'none';
        this.currentIndex = -1;
    }
    
    selecionarProduto(codigo, produtos = null) {
        if (this.produtosSelecionados.has(codigo)) {
            console.log(`⚠️ Produto ${codigo} já selecionado`);
            return;
        }
        
        // Encontrar dados do produto
        let produto = null;
        if (produtos) {
            produto = produtos.find(p => p.codigo === codigo);
        }
        
        if (!produto) {
            produto = {
                codigo: codigo,
                descricao: 'Produto não encontrado',
                grupo: null,
                fabricante: null
            };
        }
        
        this.produtosSelecionados.add(codigo);
        this.addProdutoTag(produto);
        this.updateFormValues();
        this.updateCounter();
        this.updateEmptyState();
        
        // Limpar busca
        this.searchInput.value = '';
        this.hideDropdown();
        
        console.log(`✅ Produto selecionado: ${codigo} - ${produto.descricao}`);
        
        // Disparar evento personalizado
        this.dispatchEvent('produto-selecionado', { produto, total: this.produtosSelecionados.size });
    }
    
    removerProduto(codigo) {
        if (!this.produtosSelecionados.has(codigo)) {
            return;
        }
        
        this.produtosSelecionados.delete(codigo);
        this.removeProdutoTag(codigo);
        this.updateFormValues();
        this.updateCounter();
        this.updateEmptyState();
        
        console.log(`❌ Produto removido: ${codigo}`);
        
        // Disparar evento personalizado
        this.dispatchEvent('produto-removido', { codigo, total: this.produtosSelecionados.size });
    }
    
    addProdutoTag(produto) {
        // Criar tag
        const tag = document.createElement('div');
        tag.className = 'produto-tag';
        tag.setAttribute('data-codigo', produto.codigo);
        tag.style.cssText = `
            display: inline-flex;
            align-items: center;
            background: linear-gradient(135deg, #0d6efd, #0b5ed7);
            color: white;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.75rem;
            font-weight: 500;
            margin: 2px;
            cursor: pointer;
            transition: all 0.2s ease;
            max-width: 300px;
        `;
        
        tag.innerHTML = `
            <span class="produto-tag-codigo fw-bold me-2">${produto.codigo}</span>
            <span class="produto-tag-nome" title="${produto.descricao}" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;">${produto.descricao}</span>
            <span class="produto-tag-remove ms-2" title="Remover produto" style="background: rgba(255,255,255,0.3); border-radius: 50%; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                <i class="fas fa-times" style="font-size: 0.6rem;"></i>
            </span>
        `;
        
        // Efeitos hover
        tag.addEventListener('mouseenter', () => {
            tag.style.background = 'linear-gradient(135deg, #0b5ed7, #0a58ca)';
            tag.style.transform = 'translateY(-1px)';
        });
        
        tag.addEventListener('mouseleave', () => {
            tag.style.background = 'linear-gradient(135deg, #0d6efd, #0b5ed7)';
            tag.style.transform = 'translateY(0)';
        });
        
        // Event listener para remoção
        tag.querySelector('.produto-tag-remove').addEventListener('click', (e) => {
            e.stopPropagation();
            this.removerProduto(produto.codigo);
        });
        
        this.tagsContainer.appendChild(tag);
    }
    
    removeProdutoTag(codigo) {
        const tag = this.tagsContainer.querySelector(`[data-codigo="${codigo}"]`);
        if (tag) {
            tag.remove();
        }
    }
    
    updateCounter() {
        this.counter.textContent = this.produtosSelecionados.size;
    }
    
    updateEmptyState() {
        if (this.produtosSelecionados.size === 0) {
            this.emptyState.style.display = 'block';
        } else {
            this.emptyState.style.display = 'none';
        }
    }
    
    updateFormValues() {
        // Remover inputs hidden existentes
        const existingInputs = this.container.querySelectorAll('input[name="produto"]');
        existingInputs.forEach(input => input.remove());
        
        // Criar novos inputs hidden
        this.produtosSelecionados.forEach(codigo => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'produto';
            input.value = codigo;
            this.container.appendChild(input);
        });
        
        console.log(`📝 Form values atualizados: ${Array.from(this.produtosSelecionados).join(', ')}`);
        
        // Disparar evento para atualizar filtros se a função existir
        if (typeof window.submitFilters === 'function') {
            setTimeout(() => window.submitFilters(), 100);
        }
    }
    
    loadInitialValues() {
        // Carregar valores iniciais dos inputs hidden existentes
        const existingInputs = document.querySelectorAll(`input[name="produto"]`);
        const initialCodes = Array.from(existingInputs)
            .map(input => input.value)
            .filter(value => value.trim() !== '');
        
        console.log(`🔄 Carregando valores iniciais: ${initialCodes.join(', ')}`);
        
        if (initialCodes.length > 0) {
            initialCodes.forEach(codigo => {
                this.produtosSelecionados.add(codigo);
                this.addProdutoTag({
                    codigo: codigo,
                    descricao: `Produto ${codigo}`,
                    grupo: null,
                    fabricante: null
                });
            });
            this.updateCounter();
            this.updateEmptyState();
        }
    }
    
    handleKeyboardNavigation(e) {
        if (this.dropdown.style.display === 'none') return;
        
        const items = this.dropdown.querySelectorAll('.produto-search-item[data-codigo]');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.currentIndex = Math.min(this.currentIndex + 1, items.length - 1);
                this.updateSelection(items);
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.currentIndex = Math.max(this.currentIndex - 1, 0);
                this.updateSelection(items);
                break;
                
            case 'Enter':
                e.preventDefault();
                if (this.currentIndex >= 0 && items[this.currentIndex]) {
                    const codigo = items[this.currentIndex].getAttribute('data-codigo');
                    this.selecionarProduto(codigo);
                }
                break;
                
            case 'Escape':
                this.hideDropdown();
                this.searchInput.blur();
                break;
        }
    }
    
    updateSelection(items) {
        items.forEach((item, index) => {
            if (index === this.currentIndex) {
                item.style.backgroundColor = '#e9ecef';
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.style.backgroundColor = 'white';
            }
        });
    }
    
    // Métodos públicos
    limparTodos() {
        if (this.produtosSelecionados.size === 0) {
            console.log('⚠️ Nenhum produto para limpar');
            return;
        }
        
        const count = this.produtosSelecionados.size;
        if (confirm(`Deseja remover todos os ${count} produtos selecionados?`)) {
            console.log(`🧹 Limpando ${count} produtos`);
            
            this.produtosSelecionados.clear();
            
            // Remover todas as tags
            this.tagsContainer.querySelectorAll('.produto-tag').forEach(tag => tag.remove());
            
            this.updateFormValues();
            this.updateCounter();
            this.updateEmptyState();
            
            this.dispatchEvent('produtos-limpos', { count });
        }
    }
    
    getProdutosSelecionados() {
        return Array.from(this.produtosSelecionados);
    }
    
    setProdutos(codigos) {
        console.log(`🔧 Definindo produtos: ${codigos.join(', ')}`);
        
        this.produtosSelecionados.clear();
        this.tagsContainer.querySelectorAll('.produto-tag').forEach(tag => tag.remove());
        
        codigos.forEach(codigo => {
            if (codigo.trim()) {
                this.produtosSelecionados.add(codigo.trim());
                this.addProdutoTag({
                    codigo: codigo.trim(),
                    descricao: `Produto ${codigo.trim()}`,
                    grupo: null,
                    fabricante: null
                });
            }
        });
        
        this.updateFormValues();
        this.updateCounter();
        this.updateEmptyState();
    }
    
    // Utilitários
    dispatchEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        this.container.dispatchEvent(event);
        console.log(`📡 Evento disparado: ${eventName}`, detail);
    }
}

// Exportar para uso global
window.ProdutoSearchTags = ProdutoSearchTags;

// Log de carregamento
console.log('✅ ProdutoSearchTags v2.0 carregado com sucesso!');

// Auto-inicialização para debug
window.addEventListener('load', function() {
    console.log('🌍 Window loaded - ProdutoSearchTags disponível:', typeof window.ProdutoSearchTags);
});
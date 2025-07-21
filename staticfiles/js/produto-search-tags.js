// static/js/produto-search-tags.js
// Sistema de Busca de Produtos - VERSÃO FINAL LIMPA

class ProdutoSearchTags {
    constructor(containerId, options = {}) {
        console.log('🚀 Inicializando ProdutoSearchTags para: ' + containerId);
        
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.produtosSelecionados = new Map();
        this.searchTimeout = null;
        this.isProcessingClick = false;
        
        this.options = {
            placeholder: '🔍 Digite para buscar produtos...',
            minChars: 2,
            debounceTime: 300,
            maxResults: 10,
            apiUrl: '/gestor/api/produtos/buscar/',
            emptyMessage: 'Nenhum produto selecionado',
            autoSubmit: false,
            ...options
        };
        
        if (!this.container) {
            console.error('❌ Container não encontrado: ' + containerId);
            return;
        }
        
        this.init();
    }
    
    init() {
        this.createInterface();
        this.setupEvents();
        this.loadExistingValues();
        console.log('✅ Sistema de busca inicializado');
    }
    
    createInterface() {
        this.container.innerHTML = `
            <div class="produto-search-wrapper">
                <!-- Campo de busca -->
                <div class="input-group input-group-sm">
                    <input 
                        type="text" 
                        class="form-control produto-search-input" 
                        placeholder="${this.options.placeholder}"
                        autocomplete="off"
                    >
                    <button class="btn btn-outline-secondary clear-btn" type="button" title="Limpar todos">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                
                <!-- Dropdown de resultados -->
                <div class="produto-dropdown"></div>
                
                <!-- Área de tags -->
                <div class="produtos-tags-area">
                    <div class="empty-message text-muted text-center">
                        <i class="fas fa-info-circle me-1"></i>
                        ${this.options.emptyMessage}
                    </div>
                </div>
                
                <!-- Contador -->
                <div class="mt-2 text-muted" style="font-size: 0.8rem;">
                    <i class="fas fa-list-ol me-1"></i>
                    <span class="produto-counter">0</span> produto(s) selecionado(s)
                </div>
            </div>
        `;
        
        // Referenciar elementos
        this.searchInput = this.container.querySelector('.produto-search-input');
        this.dropdown = this.container.querySelector('.produto-dropdown');
        this.tagsArea = this.container.querySelector('.produtos-tags-area');
        this.emptyMessage = this.container.querySelector('.empty-message');
        this.counter = this.container.querySelector('.produto-counter');
        this.clearBtn = this.container.querySelector('.clear-btn');
        
        // Guardar instância no container
        this.container.produtoSearchInstance = this;
    }
    
    setupEvents() {
        // Busca com debounce
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length >= this.options.minChars) {
                this.searchTimeout = setTimeout(() => this.buscarProdutos(query), this.options.debounceTime);
            } else {
                this.hideDropdown();
            }
        });
        
        // Botão limpar
        this.clearBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.limparTodos();
        });
        
        // Prevenir submit do form quando clicar nos botões
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('.clear-btn')) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        // Fechar dropdown ao clicar fora
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });
        
        // Teclas especiais
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideDropdown();
                this.searchInput.blur();
            }
        });
        
        // Prevenir blur durante processamento
        this.searchInput.addEventListener('blur', (e) => {
            if (this.isProcessingClick) {
                e.preventDefault();
                this.searchInput.focus();
            }
        });
    }
    
    async buscarProdutos(query) {
        console.log('🔍 Buscando: "' + query + '"');
        
        this.showLoading();
        
        try {
            const excludeCodes = Array.from(this.produtosSelecionados.keys()).join(',');
            const url = this.options.apiUrl + '?q=' + encodeURIComponent(query) + '&exclude=' + excludeCodes + '&limit=' + this.options.maxResults;
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error('HTTP ' + response.status + ': ' + response.statusText);
            }
            
            const data = await response.json();
            
            if (data.success && data.produtos) {
                this.mostrarResultados(data.produtos);
            } else {
                this.showMessage('Nenhum produto encontrado', 'text-muted');
            }
            
        } catch (error) {
            console.error('❌ Erro na busca:', error);
            this.showMessage('Erro: ' + error.message, 'text-danger');
        }
    }
    
    mostrarResultados(produtos) {
        if (produtos.length === 0) {
            this.showMessage('Nenhum resultado encontrado', 'text-muted');
            return;
        }
        
        const html = produtos.map(produto => `
            <div class="produto-item" data-codigo="${produto.codigo}">
                <div class="fw-bold text-primary" style="font-size: 0.9rem;">${produto.codigo}</div>
                <div style="font-size: 0.85rem;">${produto.descricao}</div>
                ${produto.grupo ? `<small class="text-muted"><i class="fas fa-layer-group me-1"></i>${produto.grupo}</small>` : ''}
            </div>
        `).join('');
        
        this.dropdown.innerHTML = html;
        
        // ESTRATÉGIA MÚLTIPLA para capturar clique
        this.dropdown.querySelectorAll('.produto-item').forEach(item => {
            const codigo = item.dataset.codigo;
            const produto = produtos.find(p => p.codigo === codigo);
            
            // mousedown (mais rápido que click)
            item.addEventListener('mousedown', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.isProcessingClick = true;
                
                setTimeout(() => {
                    this.selecionarProduto(produto);
                    this.isProcessingClick = false;
                }, 10);
            });
            
            // click (backup)
            item.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!this.isProcessingClick) {
                    this.selecionarProduto(produto);
                }
            });
        });
        
        this.showDropdown();
    }
    
    selecionarProduto(produto) {
        console.log('✅ Selecionando: ' + produto.codigo + ' - ' + produto.descricao);
        
        // Verificar duplicata
        if (this.produtosSelecionados.has(produto.codigo)) {
            this.hideDropdown();
            this.searchInput.value = '';
            return;
        }
        
        try {
            // Adicionar aos selecionados
            this.produtosSelecionados.set(produto.codigo, produto);
            
            // Criar tag visual
            this.criarTag(produto);
            
            // Atualizar formulário e interface
            this.atualizarFormulario();
            this.atualizarContador();
            this.atualizarEmptyState();
            
            // Limpar busca
            this.searchInput.value = '';
            this.hideDropdown();
            
            console.log('✅ Produto ' + produto.codigo + ' selecionado com sucesso!');
            
        } catch (error) {
            console.error('❌ Erro ao selecionar produto:', error);
        }
    }
    
    criarTag(produto) {
        const tag = document.createElement('span');
        tag.className = 'produto-tag';
        tag.dataset.codigo = produto.codigo;
        tag.innerHTML = `
            <span class="me-1">${produto.codigo}</span>
            <span class="produto-tag-remove" title="Remover">×</span>
        `;
        
        // Evento de remoção
        const removeBtn = tag.querySelector('.produto-tag-remove');
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.removerProduto(produto.codigo);
        });
        
        this.tagsArea.appendChild(tag);
    }
    
    removerProduto(codigo) {
        console.log('❌ Removendo: ' + codigo);
        
        // Remover do Map
        this.produtosSelecionados.delete(codigo);
        
        // Remover tag visual
        const tag = this.tagsArea.querySelector('[data-codigo="' + codigo + '"]');
        if (tag) {
            tag.remove();
        }
        
        // Atualizar interface
        this.atualizarFormulario();
        this.atualizarContador();
        this.atualizarEmptyState();
    }
    
    atualizarFormulario() {
        // Remover inputs existentes APENAS deste container
        const existingInputs = this.container.querySelectorAll('input[name="produto"]');
        existingInputs.forEach(input => input.remove());
        
        // Criar novos inputs hidden
        this.produtosSelecionados.forEach((produto, codigo) => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'produto';
            input.value = codigo;
            input.className = 'produto-search-input-hidden'; // Marcar para identificação
            this.container.appendChild(input);
        });
        
        console.log('📝 Formulário atualizado: ' + this.produtosSelecionados.size + ' produtos');
    }
    
    atualizarContador() {
        this.counter.textContent = this.produtosSelecionados.size;
    }
    
    atualizarEmptyState() {
        this.emptyMessage.style.display = this.produtosSelecionados.size === 0 ? 'block' : 'none';
    }
    
    loadExistingValues() {
        // Carregar produtos já selecionados dos inputs hidden com nosso marcador
        const existingInputs = this.container.querySelectorAll('input[name="produto"].produto-search-input-hidden');
        let loaded = 0;
        
        existingInputs.forEach(input => {
            const codigo = input.value.trim();
            if (codigo && !this.produtosSelecionados.has(codigo)) {
                const produto = {
                    codigo: codigo,
                    descricao: 'Produto ' + codigo
                };
                
                this.produtosSelecionados.set(codigo, produto);
                this.criarTag(produto);
                loaded++;
            }
        });
        
        // TAMBÉM carregar dos parâmetros GET da URL (para manter após submit)
        const urlParams = new URLSearchParams(window.location.search);
        const produtosFromUrl = urlParams.getAll('produto');
        
        produtosFromUrl.forEach(codigo => {
            if (codigo && !this.produtosSelecionados.has(codigo)) {
                const produto = {
                    codigo: codigo,
                    descricao: 'Produto ' + codigo
                };
                
                this.produtosSelecionados.set(codigo, produto);
                this.criarTag(produto);
                loaded++;
            }
        });
        
        if (loaded > 0) {
            this.atualizarContador();
            this.atualizarEmptyState();
            // Garantir que os inputs hidden estejam criados
            this.atualizarFormulario();
            console.log('🔄 Carregados ' + loaded + ' produtos existentes');
        }
    }
    
    // === MÉTODOS DE EXIBIÇÃO ===
    
    showLoading() {
        this.dropdown.innerHTML = `
            <div class="text-center p-3 text-muted">
                <i class="fas fa-spinner fa-spin me-2"></i>
                Buscando produtos...
            </div>
        `;
        this.showDropdown();
    }
    
    showMessage(message, className = 'text-muted') {
        this.dropdown.innerHTML = `
            <div class="text-center p-3 ${className}">
                <i class="fas fa-info-circle me-2"></i>
                ${message}
            </div>
        `;
        this.showDropdown();
    }
    
    showDropdown() {
        this.dropdown.style.display = 'block';
    }
    
    hideDropdown() {
        this.dropdown.style.display = 'none';
    }
    
    // === MÉTODOS PÚBLICOS ===
    
    limparTodos() {
        const count = this.produtosSelecionados.size;
        if (count === 0) return;
        
        this.produtosSelecionados.clear();
        this.tagsArea.querySelectorAll('.produto-tag').forEach(tag => tag.remove());
        
        this.atualizarFormulario();
        this.atualizarContador();
        this.atualizarEmptyState();
        
        console.log('🧹 Limpados ' + count + ' produtos');
    }
    
    getProdutosSelecionados() {
        return Array.from(this.produtosSelecionados.keys());
    }
}

// Disponibilizar globalmente
window.ProdutoSearchTags = ProdutoSearchTags;

console.log('✅ ProdutoSearchTags FINAL carregado!');
/**
 * SearchableSelect Component
 * A combobox component with search functionality for selecting models
 */

const SearchableSelect = {
    name: 'SearchableSelect',
    template: `
        <div class="searchable-select" :class="{ open: isOpen }" v-click-outside="close">
            <input
                type="text"
                class="searchable-select-input"
                :value="selectedLabel"
                :placeholder="placeholder"
                @focus="open"
                @input="onInput"
                readonly
            />
            <i class="ph ph-caret-down searchable-select-arrow"></i>
            
            <div v-if="isOpen" class="searchable-select-dropdown">
                <div class="searchable-select-search">
                    <i class="ph ph-magnifying-glass searchable-select-search-icon"></i>
                    <input
                        ref="searchInput"
                        type="text"
                        v-model="searchQuery"
                        placeholder="Search models..."
                        @keydown.enter="selectFirst"
                        @keydown.esc="close"
                        @keydown.down="navigateDown"
                        @keydown.up="navigateUp"
                    />
                </div>
                
                <div class="searchable-select-list" ref="list">
                    <div
                        v-for="(option, index) in filteredOptions"
                        :key="option.value"
                        class="searchable-select-option"
                        :class="{ selected: modelValue === option.value, active: activeIndex === index }"
                        @click="select(option)"
                        @mouseenter="activeIndex = index"
                    >
                        <div class="searchable-select-option-text">
                            <div>{{ option.label }}</div>
                            <div v-if="option.description" class="searchable-select-option-id">{{ option.description }}</div>
                        </div>
                        <i class="ph ph-check searchable-select-option-check"></i>
                    </div>
                    
                    <div v-if="filteredOptions.length === 0 && searchQuery" class="searchable-select-empty">
                        <i class="ph ph-smiley-sad" style="font-size: 1.5rem; display: block; margin-bottom: 0.5rem;"></i>
                        No models found for "{{ searchQuery }}"<br>
                        <small>Type to search all OpenRouter models</small>
                    </div>
                    
                    <div v-if="filteredOptions.length === 0 && !searchQuery && loading" class="searchable-select-loading">
                        <i class="ph ph-spinner"></i>
                        Loading models...
                    </div>
                </div>
            </div>
        </div>
    `,
    props: {
        modelValue: String,
        options: {
            type: Array,
            default: () => []
        },
        placeholder: {
            type: String,
            default: 'Select...'
        },
        loading: {
            type: Boolean,
            default: false
        },
        fetchOptions: {
            type: Function,
            default: null
        }
    },
    data() {
        return {
            isOpen: false,
            searchQuery: '',
            activeIndex: -1,
            internalOptions: [],
            fetched: false
        };
    },
    computed: {
        allOptions() {
            return this.options.length > 0 ? this.options : this.internalOptions;
        },
        filteredOptions() {
            if (!this.searchQuery) return this.allOptions.slice(0, 100);
            const query = this.searchQuery.toLowerCase();
            return this.allOptions.filter(opt => 
                opt.label.toLowerCase().includes(query) ||
                opt.value.toLowerCase().includes(query) ||
                (opt.description && opt.description.toLowerCase().includes(query))
            ).slice(0, 100);
        },
        selectedLabel() {
            const selected = this.allOptions.find(opt => opt.value === this.modelValue);
            return selected ? selected.label : '';
        }
    },
    async mounted() {
        // Fetch options on mount if fetchOptions is provided
        if (this.fetchOptions && !this.fetched) {
            await this.fetchOptionsFn();
        }
    },
    methods: {
        async fetchOptionsFn() {
            if (this.fetchOptions) {
                this.internalOptions = await this.fetchOptions();
                this.fetched = true;
            }
        },
        open() {
            this.isOpen = true;
            this.searchQuery = '';
            this.activeIndex = -1;
            this.$nextTick(() => {
                if (this.$refs.searchInput) {
                    this.$refs.searchInput.focus();
                }
            });
            // Fetch options when opening if not fetched yet
            if (this.fetchOptions && !this.fetched) {
                this.fetchOptionsFn();
            }
        },
        close() {
            this.isOpen = false;
            this.searchQuery = '';
            this.activeIndex = -1;
        },
        onInput() {
            this.open();
        },
        select(option) {
            this.$emit('update:modelValue', option.value);
            this.close();
        },
        selectFirst() {
            if (this.filteredOptions.length > 0) {
                this.select(this.filteredOptions[0]);
            }
        },
        navigateDown() {
            if (this.activeIndex < this.filteredOptions.length - 1) {
                this.activeIndex++;
                this.scrollToActive();
            }
        },
        navigateUp() {
            if (this.activeIndex > 0) {
                this.activeIndex--;
                this.scrollToActive();
            }
        },
        scrollToActive() {
            this.$nextTick(() => {
                if (this.$refs.list) {
                    const activeEl = this.$refs.list.children[this.activeIndex];
                    if (activeEl) {
                        activeEl.scrollIntoView({ block: 'nearest' });
                    }
                }
            });
        }
    }
};

// Click outside directive
SearchableSelect.directive('click-outside', {
    beforeMount(el, binding) {
        el.clickOutsideEvent = function(event) {
            if (!(el === event.target || el.contains(event.target))) {
                binding.value(event);
            }
        };
        document.addEventListener('click', el.clickOutsideEvent);
    },
    unmounted(el) {
        document.removeEventListener('click', el.clickOutsideEvent);
    }
});

import { Search, X } from 'lucide-react';

interface SearchFilterProps {
  search: string;
  onSearchChange: (v: string) => void;
  selectedCategory: string;
  onCategoryChange: (v: string) => void;
  selectedCountry: string;
  onCountryChange: (v: string) => void;
  selectedBias: string;
  onBiasChange: (v: string) => void;
  selectedCredibility: string;
  onCredibilityChange: (v: string) => void;
  categories: string[];
  countries: string[];
}

export const SearchFilter = ({
  search, onSearchChange,
  selectedCategory, onCategoryChange,
  selectedCountry, onCountryChange,
  selectedBias, onBiasChange,
  selectedCredibility, onCredibilityChange,
  categories, countries,
}: SearchFilterProps) => {
  const hasFilters = selectedCategory || selectedCountry || selectedBias || selectedCredibility;

  return (
    <div className="border-b border-border bg-card/50">
      <div className="container max-w-6xl mx-auto px-4 py-3 space-y-3">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search topics, headlines..."
            value={search}
            onChange={e => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-sm font-body text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
          {search && (
            <button onClick={() => onSearchChange('')} className="absolute right-3 top-1/2 -translate-y-1/2">
              <X className="w-4 h-4 text-muted-foreground hover:text-foreground" />
            </button>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">Filter:</span>
          
          <FilterSelect label="Topic" value={selectedCategory} onChange={onCategoryChange} options={categories} />
          <FilterSelect label="Country" value={selectedCountry} onChange={onCountryChange} options={countries} />
          <FilterSelect label="Bias" value={selectedBias} onChange={onBiasChange} options={['left', 'center', 'right']} />
          <FilterSelect label="Credibility" value={selectedCredibility} onChange={onCredibilityChange} options={['High', 'Medium', 'Low']} />

          {hasFilters && (
            <button
              onClick={() => { onCategoryChange(''); onCountryChange(''); onBiasChange(''); onCredibilityChange(''); }}
              className="font-mono text-xs text-primary hover:text-primary/80 underline"
            >
              Clear all
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const FilterSelect = ({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) => (
  <select
    value={value}
    onChange={e => onChange(e.target.value)}
    className="font-mono text-xs bg-background border border-border rounded-sm px-2 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary appearance-none cursor-pointer"
  >
    <option value="">{label}</option>
    {options.map(o => <option key={o} value={o}>{o}</option>)}
  </select>
);

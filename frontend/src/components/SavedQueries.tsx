import { Bookmark, Clock, Star, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const savedQueries = [
  { id: 1, name: "Gaming Laptops", query: "gaming laptop RTX", count: 24 },
  { id: 2, name: "Wireless Headphones", query: "bluetooth headphones noise canceling", count: 18 },
  { id: 3, name: "Office Chairs", query: "ergonomic office chair", count: 12 },
  { id: 4, name: "Smart Watches", query: "smartwatch fitness tracker", count: 31 },
];

const quickFilters = [
  "Under $50",
  "Free Shipping",
  "Prime Delivery",
  "Top Rated",
  "On Sale",
];

export const SavedQueries = () => {
  return (
    <div className="w-80 bg-muted/30 border-r border-border p-4 space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center">
          <Bookmark className="h-5 w-5 mr-2" />
          Saved Searches
        </h2>
        <div className="space-y-2">
          {savedQueries.map((query) => (
            <Card key={query.id} className="p-3 hover:shadow-card transition-shadow cursor-pointer">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-sm text-foreground">{query.name}</h3>
                  <p className="text-xs text-muted-foreground mt-1">{query.count} results</p>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center">
          <Clock className="h-5 w-5 mr-2" />
          Quick Filters
        </h2>
        <div className="space-y-2">
          {quickFilters.map((filter) => (
            <Button
              key={filter}
              variant="outline"
              className="w-full justify-start text-sm bg-background hover:bg-accent"
            >
              {filter}
            </Button>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center">
          <Star className="h-5 w-5 mr-2" />
          Categories
        </h2>
        <div className="space-y-1">
          {["Electronics", "Fashion", "Home & Garden", "Books", "Sports", "Beauty"].map((category) => (
            <Button
              key={category}
              variant="ghost"
              className="w-full justify-start text-sm text-muted-foreground hover:text-foreground"
            >
              {category}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
};
<script lang="ts">
  import './app.css';
  import { onMount } from "svelte";
  import Comments from './Comments.svelte';

  // Core state variables
  let ingredients: string = "";
  let ingredientList: string[] = [];
  let recipes: any[] = [];
  let user: any = null;
  let selectedRecipe: any = null;
  let showRecipeModal = false;

  let loading = false;
  let searchError = "";

  let showAccountSidebar = false;

  let userRating = 0;
  let userReview = "";
  let showReviewForm = false;

  let selectedMealType = "";
  let selectedTime = "";
  let selectedDiet = "";
  let selectedIntolerances: string[] = [];
  let selectedCuisine = "";
  let activeDropdown = "";

  let availableCuisines: string[] = [];
  let availableDiets: string[] = [];
  let availableIntolerances: string[] = [];
  let availableMealTypes: string[] = [];

  let activeTab = "ingredients";
  let specificRecipeQuery = "";
  let specificRecipeResults: any[] = [];
  let specificRecipeLoading = false;

  let userFavorites: any[] = [];
  let userReviews: any[] = [];
  
  const timeOptions = [
    { value: "15", label: "<15 mins" },
    { value: "30", label: "<30 mins" },
    { value: "45", label: "<45 mins" },
    { value: "60", label: "<1 hour" },
    { value: "120", label: "<2 hours" }
  ];

  const mealTypeMapping = [
    { id: "main course", label: "MAIN COURSE", icon: "🍖" },
    { id: "breakfast", label: "BREAKFAST", icon: "☕" },
    { id: "dessert", label: "DESSERT", icon: "🍰" },
    { id: "appetizer", label: "APPETIZER", icon: "🥗" },
    { id: "snack", label: "SNACK", icon: "🥨" }
  ];

  // Load current view from localStorage or default to "home"
  let currentView = localStorage.getItem("currentView") || "home";

  // Set backend API base URL configuration
  const BACKEND_BASE = import.meta.env.VITE_BACKEND_BASE || "http://localhost:8000";

  // Save current search state to localStorage to aid in page reload
  function saveSearchState() {
    localStorage.setItem('searchState', JSON.stringify({
      activeTab,
      ingredients,
      ingredientList,
      recipes,
      specificRecipeQuery,
      specificRecipeResults,
      selectedMealType,
      selectedTime,
      selectedDiet,
      selectedIntolerances,
      selectedCuisine
    }));
  }

  // Load search state from localStorage to restore previous search
  function loadSearchState() {
    const savedState = localStorage.getItem('searchState');
    if (savedState) {
      const state = JSON.parse(savedState);
      activeTab = state.activeTab || "ingredients";
      ingredients = state.ingredients || "";
      ingredientList = state.ingredientList || [];
      recipes = state.recipes || [];
      specificRecipeQuery = state.specificRecipeQuery || "";
      specificRecipeResults = state.specificRecipeResults || [];
      selectedMealType = state.selectedMealType || "";
      selectedTime = state.selectedTime || "";
      selectedDiet = state.selectedDiet || "";
      selectedIntolerances = state.selectedIntolerances || [];
      selectedCuisine = state.selectedCuisine || "";
    }
  }

  onMount(() => {
    checkAuthStatus();
    loadFilterOptions();
    loadSearchState();
  });

  // Load filter options from backend or use defaults
  async function loadFilterOptions() {
    try {
      const [cuisinesRes, dietsRes, intolerancesRes, mealTypesRes] = await Promise.all([
        fetch(`${BACKEND_BASE}/api/cuisines`),
        fetch(`${BACKEND_BASE}/api/diets`),
        fetch(`${BACKEND_BASE}/api/intolerances`),
        fetch(`${BACKEND_BASE}/api/meal-types`)
      ]);

      availableCuisines = await cuisinesRes.json();
      availableDiets = await dietsRes.json();
      availableIntolerances = await intolerancesRes.json();
      availableMealTypes = await mealTypesRes.json();
    } catch (error) {
      console.error('Error loading filter options:', error);

      availableCuisines = ["Italian", "Thai", "Mexican", "Chinese", "American", "Indian"];
      availableDiets = ["vegetarian", "vegan", "gluten free"];
      availableIntolerances = ["dairy", "gluten", "peanut"];
      availableMealTypes = ["main course", "breakfast", "dessert"];
    }
  }

  // Check if user is authenticated and load their data
  async function checkAuthStatus() {
    try {
      const response = await fetch(`${BACKEND_BASE}/api/user/profile`, {
        method: 'GET',
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          user = data.user;
          await loadUserData();
        }
      }
    } catch (error) {
      console.log('User not logged in');
    }
  }

  // Load user-specific data such as favorites and reviews
  async function loadUserData() {
    if (!user) return;
    
    try {
      console.log('Loading user data...');
      
      // Load favorites
      try {
        const favoritesRes = await fetch(`${BACKEND_BASE}/api/user/favorites`, { 
          credentials: 'include',
          headers: { 'Accept': 'application/json' }
        });
        
        if (favoritesRes.ok) {
          const favData = await favoritesRes.json();
          if (favData.success) {
            userFavorites = favData.favorites || [];
            console.log(`Loaded ${userFavorites.length} favorites`);
          }
        }
      } catch (error) {
        console.log('Failed to load favorites:', error);
      }

      // Load reviews
      try {
        const reviewsRes = await fetch(`${BACKEND_BASE}/api/user/reviews`, { 
          credentials: 'include',
          headers: { 'Accept': 'application/json' }
        });
        
        if (reviewsRes.ok) {
          const reviewData = await reviewsRes.json();
          if (reviewData.success) {
            // Ensure all reviews have fallback images
            userReviews = (reviewData.reviews || []).map((review: any) => ({
              ...review,
              recipe_image: review.recipe_image || '/Temp_Image.jpg'
            }));
            console.log(`Loaded ${userReviews.length} reviews`);
          }
        }
      } catch (error) {
        console.log('Failed to load reviews:', error);
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  }

  // Redirect user to backend login endpoint
  function login() {
    window.location.href = `${BACKEND_BASE}/login`;
  }

  // Redirect user to backend logout endpoint
  function logout() {
    window.location.href = `${BACKEND_BASE}/logout`;
  }

  // Add ingredient to the list and save state
  function addIngredient() {
    const trimmed = ingredients.trim().toLowerCase();
    saveSearchState();
    if (trimmed && !ingredientList.includes(trimmed)) {
      ingredientList = [...ingredientList, trimmed];
      ingredients = "";
      saveSearchState();
    }
  }

  // Remove ingredient from the list and search for recipes if any ingredients remain
  function removeIngredient(ing: string) {
    ingredientList = ingredientList.filter(i => i !== ing);
    if (ingredientList.length > 0) {
      searchRecipes();
    } else {
      recipes = [];
      saveSearchState();
    }
  }

  // Search for recipes based on ingredients and filters
  async function searchRecipes() {
    loading = true;
    searchError = "";
    
    try {
      // Determine search term based on ingredient list or user input
      let searchTerm = "";
      if (ingredientList.length > 0) {
        searchTerm = ingredientList.join(',');
      } else if (ingredients.trim()) {
        searchTerm = ingredients.trim().toLowerCase();
      } else {
        recipes = [];
        loading = false;
        return;
      }

      const params = new URLSearchParams({
        ingredients: searchTerm
      });

      // Add filter parameters if selected
      if (selectedCuisine) params.append('cuisine', selectedCuisine);
      if (selectedDiet) params.append('diet', selectedDiet);
      if (selectedIntolerances.length > 0) params.append('intolerances', selectedIntolerances.join(','));
      if (selectedTime) params.append('maxReadyTime', selectedTime);
      if (selectedMealType) params.append('type', selectedMealType);

      params.append('number', '6');

      const url = `${BACKEND_BASE}/recipes?${params.toString()}`;
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const recipeResults = await res.json();

      if (!Array.isArray(recipeResults)) {
        searchError = recipeResults.error || "Invalid response format";
        recipes = [];
        loading = false;
        return;
      }

      if (recipeResults.length === 0) {
        searchError = "No recipes found for these ingredients. Try different ingredients or remove some filters.";
        recipes = [];
        loading = false;
        return;
      }

      // Process and normalize recipe data for consistent frontend display
      recipes = recipeResults.map((r: any) => ({
        id: r.id,
        title: r.title || `Recipe ${r.id}`,
        image: r.image || '/Temp_Image.jpg', 
        calories: r.calories || r.nutrition?.nutrients?.find((n: any) => n.name === 'Calories')?.amount || 0,
        rating: r.spoonacularScore !== undefined ? Math.round(r.spoonacularScore / 20 * 10) / 10 : 3.0,
        cuisines: r.cuisines && r.cuisines.length > 0 ? r.cuisines : ["International"],
        readyInMinutes: r.readyInMinutes || 30,
        servings: r.servings || 1,
        vegetarian: r.vegetarian || false,
        vegan: r.vegan || false,
        glutenFree: r.glutenFree || false,
        dairyFree: r.dairyFree || false,
        dishTypes: r.dishTypes || ["main course"],
        extendedIngredients: r.extendedIngredients || [],
        analyzedInstructions: r.analyzedInstructions || [],
        nutrition: r.nutrition || {
          nutrients: [
            { name: "Calories", amount: r.calories || 0, unit: "kcal" },
            { name: "Fat", amount: 0, unit: "g" },
            { name: "Carbohydrates", amount: 0, unit: "g" },
            { name: "Protein", amount: 0, unit: "g" }
          ]
        }
      }));
      saveSearchState();
      
    } catch (error) {
      console.error("Error fetching recipes:", error);
      searchError = `Failed to fetch recipes: ${(error as Error).message}`;
      recipes = [];
    } finally {
      loading = false;
    }
  }

  // Search for specific recipes based on user query
  async function searchSpecificRecipe() {
    if (!specificRecipeQuery.trim()) return;
    
    specificRecipeLoading = true;
    searchError = "";
    
    try {
      const params = new URLSearchParams({
        query: specificRecipeQuery.trim(),
        number: '6'
      });

      const url = `${BACKEND_BASE}/recipes?${params.toString()}`;
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const results = await res.json();
      
      if (!Array.isArray(results)) {
        searchError = results.error || "Invalid response format";
        specificRecipeResults = [];
        return;
      }

      if (results.length === 0) {
        searchError = "No recipes found for this search. Try different keywords.";
        specificRecipeResults = [];
        return;
      }

      // Process and normalize specific recipe data for consistent frontend display
      specificRecipeResults = results.map((r: any) => ({
        id: r.id,
        title: r.title || `Recipe ${r.id}`,
        image: r.image || '/Temp_Image.jpg',
        calories: r.calories || r.nutrition?.nutrients?.find((n: any) => n.name === 'Calories')?.amount || 0,
        rating: r.spoonacularScore !== undefined ? Math.round(r.spoonacularScore / 20 * 10) / 10 : 3.0,
        cuisines: r.cuisines && r.cuisines.length > 0 ? r.cuisines : ["International"],
        readyInMinutes: r.readyInMinutes || 30,
        servings: r.servings || 1,
        vegetarian: r.vegetarian || false,
        vegan: r.vegan || false,
        glutenFree: r.glutenFree || false,
        dairyFree: r.dairyFree || false,
        dishTypes: r.dishTypes || ["main course"],
        extendedIngredients: r.extendedIngredients || [],
        analyzedInstructions: r.analyzedInstructions || [],
        nutrition: r.nutrition || {
          nutrients: [
            { name: "Calories", amount: r.calories || 0, unit: "kcal" },
            { name: "Fat", amount: 0, unit: "g" },
            { name: "Carbohydrates", amount: 0, unit: "g" },
            { name: "Protein", amount: 0, unit: "g" }
          ]
        }
      }));

      saveSearchState();
      
    } catch (error) {
      console.error("Error searching specific recipes:", error);
      searchError = `Failed to search recipes: ${(error as Error).message}`;
      specificRecipeResults = [];
    } finally {
      specificRecipeLoading = false;
    }
  }

  // Switch between ingredient search and specific recipe search tabs
  function switchTab(tab: string) {
    activeTab = tab;
    if (tab === "ingredients") {
      specificRecipeResults = [];
      specificRecipeQuery = "";
    } else {
      recipes = [];
      ingredientList = [];
      ingredients = "";
    }
    searchError = "";
    saveSearchState();
  }

  // Toggle favorite status for a recipe
  async function toggleFavorite(recipe: any) {
    if (!user) {
      alert('Please log in to favorite recipes');
      return;
    }

    try {
      const isFavorited = userFavorites.some(fav => fav.id === recipe.id);
      
      if (isFavorited) {
        // Remove from favorites
        const response = await fetch(`${BACKEND_BASE}/api/favorites/${recipe.id}`, {
          method: 'DELETE',
          credentials: 'include',
          headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
          userFavorites = userFavorites.filter(fav => fav.id !== recipe.id);
          console.log('Removed from favorites');
        }
      } else {
        // Add to favorites
        const response = await fetch(`${BACKEND_BASE}/api/favorites`, {
          method: 'POST',
          credentials: 'include',
          headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ 
            recipeId: recipe.id, 
            recipe: recipe 
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
          userFavorites = [...userFavorites, recipe];
          console.log('Added to favorites');
        }
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      alert('Error updating favorites. Please try again.');
    }
  }

  function isRecipeFavorited(recipeId: number): boolean {
    return userFavorites.some(fav => fav.id === recipeId);
  }

  async function submitReviewWithRating() {
    if (!user) {
      alert('Please log in to submit reviews');
      return;
    }
    
    if (userRating === 0) {
      alert('Please select a rating');
      return;
    }
    
    if (!userReview.trim()) {
      alert('Please write a review');
      return;
    }

    try {
      const response = await fetch(`${BACKEND_BASE}/api/reviews`, {
        method: 'POST',
        credentials: 'include',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          recipeId: selectedRecipe.id,
          rating: userRating,
          review: userReview.trim(),
          recipeTitle: selectedRecipe.title,
          recipeImage: selectedRecipe.image || '/Temp_Image.jpg'  // Ensure image is included
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // Add the new review to local state with all data
        const newReview = {
          id: result.review_id,
          recipeId: selectedRecipe.id,
          recipe_title: selectedRecipe.title,
          recipe_image: selectedRecipe.image || '/Temp_Image.jpg',  // Ensure image is included
          rating: userRating,
          review: userReview.trim(),
          createdAt: new Date().toISOString(),
          userEmail: user.email
        };
        
        userReviews = [...userReviews, newReview];
        showReviewForm = false;
        userRating = 0;
        userReview = "";
        
        alert('Review submitted successfully!');
        console.log('Review submitted:', newReview);
      }
      
    } catch (error) {
      console.error('Error submitting review:', error);
      if ((error as Error).message.includes('already reviewed')) {
        alert('You have already reviewed this recipe.');
      } else {
        alert('Error submitting review. Please try again.');
      }
    }
  }

  // Toggle dropdown visibility for filters
  function toggleDropdown(dropdown: string) {
    activeDropdown = activeDropdown === dropdown ? "" : dropdown;
  }

  // Reapply filters after any change
  function reapplyFilters() {
    if (ingredientList.length > 0 || ingredients.trim()) {
      searchRecipes();
    }
  }

  // Toggle meal type selection
  function toggleMealType(mealType: string) {
    selectedMealType = selectedMealType === mealType ? "" : mealType;
    saveSearchState();
    reapplyFilters();
  }

  // Select a filter value and toggle its state
  function selectFilter(filterType: string, value: string) {
    switch(filterType) {
      case 'time':
        selectedTime = selectedTime === value ? "" : value;
        break;
      case 'diet':
        selectedDiet = selectedDiet === value ? "" : value;
        break;
      case 'cuisine':
        selectedCuisine = selectedCuisine === value ? "" : value;
        break;
    }
    activeDropdown = "";
    saveSearchState();
    reapplyFilters();
  }

  // Toggle intolerance selection
  function toggleIntolerance(intolerance: string) {
    if (selectedIntolerances.includes(intolerance)) {
      selectedIntolerances = selectedIntolerances.filter(i => i !== intolerance);
    } else {
      selectedIntolerances = [...selectedIntolerances, intolerance];
    }
    saveSearchState();
    reapplyFilters();
  }

  // Clear all filters and reset state
  function clearAllFilters() {
    selectedMealType = "";
    selectedTime = "";
    selectedDiet = "";
    selectedIntolerances = [];
    selectedCuisine = "";
    activeDropdown = "";
    saveSearchState();
    reapplyFilters();
  }
  // Open recipe modal to view details and submit reviews
  function openRecipeModal(recipe: any) {
    selectedRecipe = recipe;
    showRecipeModal = true;
    userRating = 0;
    userReview = "";
    showReviewForm = false;
  }

  // Close recipe modal
  function closeRecipeModal() {
    showRecipeModal = false;
    selectedRecipe = null;
  }

  // Render stars based on rating
  function renderStars(rating: number) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating - fullStars >= 0.5;
    let stars = '';
    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars += '★';
      } else if (i === fullStars && hasHalfStar) {
        stars += '☆';
      } else {
        stars += '☆';
      }
    }
    return stars;
  }

  // Set user rating for the recipe
  function setRating(rating: number) {
    userRating = rating;
  }
  
  // Get nutrient value by name, rounding to the nearest integer
  function getNutrientValue(nutrients: any[], name: string): number {
    const nutrient = nutrients.find(n => n.name === name);
    return nutrient ? Math.round(nutrient.amount) : 0;
  }
  
  // Handle image loading errors by setting a fallback image
  function handleImageError(event: Event) {
    const target = event.target as HTMLImageElement;
    if (target && target.src !== '/Temp_Image.jpg') {
      console.log(`Image failed to load:`, target.src);
      target.src = '/Temp_Image.jpg';
    }
  }
  // Show home view
  function showHome() {
    currentView = "home";
    localStorage.setItem("currentView", currentView);
    showAccountSidebar = false;
  }

  // Show favorites view
  function showFavorites() {
    currentView = "favorites";
    localStorage.setItem("currentView", currentView);
    showAccountSidebar = false;
  }

  // Show reviews view
  function showReviews() {
    currentView = "reviews";
    localStorage.setItem("currentView", currentView);
    showAccountSidebar = false;
    
    // Load reviews when switching to reviews view (same as favorites)
    if (user && userReviews.length === 0) {
      loadUserData();
    }
  }
</script>

<main class="figma-main">
  <!-- HEADER -->
  <header class="figma-header">
    <div class="header-content">
      <button class="website-title" on:click={showHome}>
        🍽️ whisk
      </button>
      <div class="header-nav">
        <button class="nav-button" on:click={showHome}>
          Home
        </button>
        {#if user}
          <div class="user-menu">
            <button class="nav-button" on:click={() => (showAccountSidebar = !showAccountSidebar)}>
              👤 Account ▾
            </button>
            {#if showAccountSidebar}
              <div class="dropdown-menu">
                <div class="user-email">{user.email}</div>
                <button class="favorites-btn link-button" on:click={showFavorites}>⭐ My Favorites</button>
                <button class="reviews-btn link-button" on:click={showReviews}>📝 My Reviews</button>
                <button class="logout-btn link-button" on:click={logout}>
                  🚪 Logout
                </button>
              </div>
            {/if}
          </div>
        {:else}
          <button class="nav-button" on:click={login}>
            Login
          </button>
        {/if}
      </div>
    </div>
  </header>

  {#if currentView === "home"}
    <slot></slot>
  {/if}
{#if currentView === "home"}

  <!-- HERO SECTION -->
  <section class="hero-section">
    <div class="hero-content">
      <h2 class="hero-title">You bring the ingredients, we bring the recipes</h2>
      <p class="hero-subtitle">Recipes built around what's left in your fridge — don't waste it, taste it.</p>
    </div>
  </section>

  <!-- SEARCH SECTION -->
  <section class="search-section">
    <div class="search-tabs">
      <button class="tab-button {activeTab === 'ingredients' ? 'active' : ''}" on:click={() => switchTab('ingredients')}>
        USE MY INGREDIENTS
      </button>
      <button class="tab-button {activeTab === 'specific' ? 'active' : ''}" on:click={() => switchTab('specific')}>
        FIND SPECIFIC RECIPE
      </button>
    </div>

    <!-- Search input and buttons -->
    {#if activeTab === 'ingredients'}
      <h2 class="search-title">Search Recipes by Ingredients</h2>
    {:else}
      <h2 class="search-title">Search for Specific Recipes</h2>
    {/if}
    {#if activeTab === 'ingredients'}
      <div class="search-container">
        <input
          type="text"
          bind:value={ingredients}
          placeholder="Enter ingredients (e.g., chicken, rice, vegetables)..."
          class="search-input"
          on:keydown={e => {
            if (e.key === 'Enter') {
              e.preventDefault();
              if (ingredients.trim()) {
                addIngredient();
                if (ingredientList.length > 0) searchRecipes();
              }
            }
          }}
        />
        <button class="search-btn" on:click={() => {
          if (ingredients.trim()) {
            addIngredient();
            if (ingredientList.length > 0) searchRecipes();
          } else if (ingredientList.length > 0) {
            searchRecipes();
          }
        }} disabled={loading}>
          {#if loading}
            <span class="spinner">⏳</span>
          {:else}
            <span class="search-icon">🔍</span>
          {/if}
        </button>
      </div>
      {#if ingredientList.length > 0 || ingredients.trim()}
        <div class="ingredient-tags">
          {#each ingredientList as ing}
            <span class="ingredient-tag">
              {ing.toUpperCase()}
              <button class="remove-tag" on:click={() => removeIngredient(ing)}>×</button>
            </span>
          {/each}
          {#if ingredients.trim() && !ingredientList.includes(ingredients.trim().toLowerCase())}
            <span class="ingredient-tag pending">
              {ingredients.toUpperCase()} (press enter to add)
            </span>
          {/if}
        </div>
      {/if}
    {:else}
      <div class="search-container">
        <input
          type="text"
          bind:value={specificRecipeQuery}
          placeholder="Search for specific recipes (e.g., 'chocolate cake', 'chicken curry')..."
          class="search-input"
          on:keydown={e => {
            if (e.key === 'Enter') {
              e.preventDefault();
              searchSpecificRecipe();
            }
          }}
        />
        <button class="search-btn" on:click={searchSpecificRecipe} disabled={specificRecipeLoading}>
          {#if specificRecipeLoading}
            <span class="spinner">⏳</span>
          {:else}
            <span class="search-icon">🔍</span>
          {/if}
        </button>
      </div>
    {/if}
    
    {#if loading || specificRecipeLoading}
      <div class="debug-info loading">
        <span class="spinner">⏳</span>
        Searching for delicious recipes...
      </div>
    {/if}
    
    {#if searchError}
      <div class="debug-info error">
        ⚠️ {searchError}
      </div>
    {/if}
    
    {#if (activeTab === 'ingredients' && recipes.length === 0 && !loading && !searchError && ingredientList.length > 0) || 
         (activeTab === 'specific' && specificRecipeResults.length === 0 && !specificRecipeLoading && !searchError && specificRecipeQuery.trim())}
      <div class="debug-info warning">
        ℹ️ No recipes found. Try different {activeTab === 'ingredients' ? 'ingredients' : 'search terms'}.
      </div>
    {/if}
  </section>

  {#if ingredientList.length > 0 && activeTab === 'ingredients'}
    <section class="filters-section">
      <div class="filters-container">
        <div class="ingredient-display">
          <h3>
            <span class="section-icon">🌱</span>
            MY INGREDIENTS:
          </h3>
          <div class="current-ingredients">
            {#each ingredientList as ing}
              <span class="ingredient-tag">
                <span class="tag-icon">🥬</span>
                {ing.toUpperCase()}
                <button class="remove-tag" on:click={() => removeIngredient(ing)}>
                  <span class="close-icon">×</span>
                </button>
              </span>
            {/each}
          </div>
        </div>
        <div class="meal-type-section">
          <div class="meal-type-grid">
            {#each mealTypeMapping as mealType}
              <button 
                class="meal-type-card {selectedMealType === mealType.id ? 'selected' : ''}"
                on:click={() => toggleMealType(mealType.id)}
              >
                <div class="meal-icon">{mealType.icon}</div>
                <div class="meal-label">{mealType.label}</div>
              </button>
            {/each}
          </div>
        </div>
        <div class="filter-dropdowns">
          <div class="filter-dropdown">
            <button class="filter-btn {selectedTime ? 'active' : ''}" on:click={() => toggleDropdown('time')}>
              <span class="filter-icon">⏰</span>
              <span class="filter-text">TIME</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            {#if activeDropdown === 'time'}
              <div class="dropdown-content">
                {#each timeOptions as option}
                  <button 
                    class="dropdown-option {selectedTime === option.value ? 'selected' : ''}"
                    on:click={() => selectFilter('time', option.value)}
                  >
                    <span class="option-icon">⏰</span>
                    <span class="option-text">{option.label}</span>
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <div class="filter-dropdown">
            <button class="filter-btn {selectedDiet ? 'active' : ''}" on:click={() => toggleDropdown('diet')}>
              <span class="filter-icon">🌱</span>
              <span class="filter-text">DIET</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            {#if activeDropdown === 'diet'}
              <div class="dropdown-content">
                {#each availableDiets as option}
                  <button 
                    class="dropdown-option {selectedDiet === option ? 'selected' : ''}"
                    on:click={() => selectFilter('diet', option)}
                  >
                    <span class="option-icon">🌱</span>
                    <span class="option-text">{option}</span>
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <div class="filter-dropdown">
            <button class="filter-btn {selectedIntolerances.length > 0 ? 'active' : ''}" on:click={() => toggleDropdown('intolerance')}>
              <span class="filter-icon">🛡️</span>
              <span class="filter-text">INTOLERANCES</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            {#if activeDropdown === 'intolerance'}
              <div class="dropdown-content">
                {#each availableIntolerances as option}
                  <button 
                    class="dropdown-option {selectedIntolerances.includes(option) ? 'selected' : ''}"
                    on:click={() => toggleIntolerance(option)}
                  >
                    <span class="option-icon">🛡️</span>
                    <span class="option-text">{option} {selectedIntolerances.includes(option) ? '✓' : ''}</span>
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <div class="filter-dropdown">
            <button class="filter-btn {selectedCuisine ? 'active' : ''}" on:click={() => toggleDropdown('cuisine')}>
              <span class="filter-icon">🌍</span>
              <span class="filter-text">CUISINE</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            {#if activeDropdown === 'cuisine'}
              <div class="dropdown-content">
                {#each availableCuisines as option}
                 <button 
                   class="dropdown-option {selectedCuisine === option ? 'selected' : ''}"
                   on:click={() => selectFilter('cuisine', option)}
                 >
                   <span class="option-icon">🌍</span>
                   <span class="option-text">{option}</span>
                 </button>
               {/each}
             </div>
           {/if}
         </div>
       </div>
       {#if selectedTime || selectedDiet || selectedIntolerances.length > 0 || selectedCuisine || selectedMealType}
         <div class="active-filters">
           <span class="filter-label">
             <span class="filter-label-icon">🔗</span>
             Active filters:
           </span>
           {#if selectedMealType}
             <span class="active-filter-tag">
               {mealTypeMapping.find(m => m.id === selectedMealType)?.label}
               <button on:click={() => toggleMealType(selectedMealType)}>×</button>
             </span>
           {/if}
           {#if selectedTime}
             <span class="active-filter-tag">
               {timeOptions.find(t => t.value === selectedTime)?.label}
               <button on:click={() => selectFilter('time', selectedTime)}>×</button>
             </span>
           {/if}
           {#if selectedDiet}
             <span class="active-filter-tag">
               {selectedDiet}
               <button on:click={() => selectFilter('diet', selectedDiet)}>×</button>
             </span>
           {/if}
           {#each selectedIntolerances as intolerance}
             <span class="active-filter-tag">
               {intolerance}
               <button on:click={() => toggleIntolerance(intolerance)}>×</button>
             </span>
           {/each}
           {#if selectedCuisine}
             <span class="active-filter-tag">
               {selectedCuisine}
               <button on:click={() => selectFilter('cuisine', selectedCuisine)}>×</button>
             </span>
           {/if}
           <button class="clear-filters-btn" on:click={clearAllFilters}>
             <span class="clear-icon">🧹</span>
             Clear All
           </button>
         </div>
       {/if}
     </div>
   </section>
 {/if}

 <!-- RECIPE RESULTS -->
 {#if (activeTab === 'ingredients' && recipes.length > 0) || (activeTab === 'specific' && specificRecipeResults.length > 0)}
   <section class="results-section">
     <h2 class="section-title">
       <span class="title-icon">🍽️</span>
       RECIPE RESULTS ({activeTab === 'ingredients' ? recipes.length : specificRecipeResults.length})
     </h2>
     <div class="recipes-grid">
       {#each (activeTab === 'ingredients' ? recipes : specificRecipeResults) as recipe, index}
         <div 
           class="recipe-card clickable" 
           style="animation-delay: {index * 0.1}s"
           on:click={() => openRecipeModal(recipe)} 
           on:keydown={(e) => e.key === 'Enter' && openRecipeModal(recipe)} 
           tabindex="0"
         >
           <div class="recipe-image-container">
             <img 
               src={recipe.image} 
               alt={recipe.title} 
               class="recipe-image" 
               on:error={handleImageError}
             />
             <div class="recipe-overlay">
               <button class="quick-view-btn">
                 <span class="btn-icon">👁️</span>
                 View Recipe
               </button>
             </div>
             {#if user}
               <button 
                 class="favorite-heart {isRecipeFavorited(recipe.id) ? 'favorited' : ''}"
                 on:click|stopPropagation={() => toggleFavorite(recipe)}
               >
                 {isRecipeFavorited(recipe.id) ? '❤️' : '🤍'}
               </button>
             {/if}
           </div>
           <div class="recipe-info">
             <h3 class="recipe-title">{recipe.title.toUpperCase()}</h3>
             <div class="rating-stars">{renderStars(recipe.rating)}</div>
             <div class="recipe-meta">
               <span class="cuisine">
                 <span class="meta-icon">🌍</span>
                 {recipe.cuisines[0]}
               </span>
               <span class="calories">
                 <span class="meta-icon">🔥</span>
                 {recipe.calories} cal
               </span>
             </div>
             {#if recipe.vegan}
               <div class="dietary-badge vegan">V</div>
             {/if}
             {#if recipe.glutenFree}
               <div class="dietary-badge gluten-free">GF</div>
             {/if}
           </div>
         </div>
       {/each}
     </div>
   </section>
 {/if}

 <!-- RECIPE MODAL -->
  {:else if currentView === "reviews"}
    <section class="reviews-page">
      <div class="reviews-container">
        <h2 class="reviews-page-title">
          <span class="title-icon">📝</span>
          MY REVIEWS ({userReviews.length})
        </h2>
        
        {#if userReviews.length === 0}
          <div class="empty-state-reviews">
            <div class="empty-icon">📝</div>
            <h3>No Reviews Yet</h3>
            <p>Start exploring recipes and share your thoughts with the community!</p>
            <button class="cta-button" on:click={showHome}>
              <span>🔍</span>
              Find Recipes
            </button>
          </div>
        {:else}
          <div class="reviews-grid">
            {#each userReviews as review, index}
              <div class="review-card-modern" style="animation-delay: {index * 0.1}s">
                <div class="review-image-wrapper">
                  <img 
                    src={review.recipe_image || '/Temp_Image.jpg'} 
                    alt={review.recipe_title || 'Recipe'} 
                    class="review-recipe-img"
                    on:error={handleImageError}
                  />
                  <div class="image-overlay">
                    <span class="view-recipe-text">View Recipe</span>
                  </div>
                </div>
                
                <div class="review-details">
                  <div class="review-header-modern">
                    <h3 class="recipe-title-modern">{review.recipe_title || `Recipe ${review.recipeId}`}</h3>
                    <div class="date-badge-modern">
                      {new Date(review.createdAt).toLocaleDateString('en-US', { 
                        month: 'numeric', 
                        day: 'numeric', 
                        year: '2-digit' 
                      })}
                    </div>
                  </div>
                  
                  <div class="rating-stars-modern">
                    {#each Array(5) as _, i}
                      <span class="star {i < review.rating ? 'filled' : 'empty'}">★</span>
                    {/each}
                  </div>
                  
                  <div class="review-text-wrapper">
                    <div class="quote-mark-start">"</div>
                    <p class="review-text-modern">{review.review}</p>
                    <div class="quote-mark-end">"</div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </section>
  {:else if currentView === "favorites"}
    <section class="favorites-section">
      <h2 class="section-title">
        <span class="title-icon">⭐</span>
        MY FAVORITES ({userFavorites.length})
      </h2>
      {#if userFavorites.length === 0}
        <p class="empty-message">You have no favorited recipes yet.</p>
      {:else}
        <div class="recipes-grid">
          {#each userFavorites as recipe, index}
            <div 
              class="recipe-card clickable"
              style="animation-delay: {index * 0.1}s"
              on:click={() => openRecipeModal(recipe)}
              tabindex="0"
            >
              <div class="recipe-image-container">
                <img 
                  src={recipe.image} 
                  alt={recipe.title} 
                  class="recipe-image"
                  on:error={handleImageError}
                />
                <div class="recipe-overlay">
                  <button class="quick-view-btn">
                    <span class="btn-icon">👁️</span>
                    View Recipe
                  </button>
                </div>
                <button
                  class="favorite-heart favorited"
                  on:click|stopPropagation={() => toggleFavorite(recipe)}
                >
                  ❤️
                </button>
              </div>
              <div class="recipe-info">
                <h3 class="recipe-title">{recipe.title.toUpperCase()}</h3>
                <div class="rating-stars">{renderStars(recipe.rating)}</div>
                <div class="recipe-meta">
                  <span class="cuisine">
                    <span class="meta-icon">🌍</span>
                    {recipe.cuisines[0]}
                  </span>
                  <span class="calories">
                    <span class="meta-icon">🔥</span>
                    {recipe.calories} cal
                  </span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>
  {/if}
 {#if showRecipeModal && selectedRecipe}
   <div class="recipe-detail-modal" on:click={closeRecipeModal}>
     <div class="modal-content" on:click|stopPropagation>
       <button class="modal-close-btn" on:click={closeRecipeModal}>
         <span class="close-icon">×</span>
       </button>
       
       <div class="recipe-header-compact">
         <div class="recipe-header-content">
           <h1 class="recipe-detail-title">{selectedRecipe.title}</h1>
           
           <div class="recipe-rating-info">
             <div class="rating-display">
               <div class="rating-stars-large">{renderStars(selectedRecipe.rating)}</div>
               <span class="rating-number">{selectedRecipe.rating}</span>
               <span class="cuisine-type">| {selectedRecipe.cuisines[0]} Cuisine</span>
             </div>
           </div>
           
           <div class="recipe-stats-bar-compact">
             <div class="stat-item">
               <strong>Prep:</strong> {Math.round(selectedRecipe.readyInMinutes * 0.3)} min
             </div>
             <div class="stat-item">
               <strong>Cook:</strong> {Math.round(selectedRecipe.readyInMinutes * 0.7)} min
             </div>
             <div class="stat-item">
               <strong>Serves:</strong> {selectedRecipe.servings}
             </div>
           </div>
           
           <div class="recipe-actions">
             <button class="favorite-btn" on:click={() => toggleFavorite(selectedRecipe)}>
               <span class="heart-icon">
                 {isRecipeFavorited(selectedRecipe.id) ? '❤️' : '🤍'}
               </span>
               Favorite
             </button>
             {#if user}
               <button class="rate-btn" on:click={() => showReviewForm = !showReviewForm}>
                 <span class="star-icon">⭐</span>
                 Write Review
               </button>
             {/if}
           </div>
         </div>
       </div>
       
       <div class="recipe-scrollable-content">
         <div class="recipe-body">
           <div class="recipe-left">
             <img src={selectedRecipe.image} alt={selectedRecipe.title} class="recipe-detail-image" on:error={handleImageError} />
             
             <div class="nutrition-box">
               <h3>
                 Nutrition Info <span class="per-serving">(per serving)</span>
               </h3>
               <div class="nutrition-grid">
                 <div class="nutrition-item">
                   <span class="nutrition-value">{getNutrientValue(selectedRecipe.nutrition?.nutrients || [], 'Calories')}</span>
                   <span class="nutrition-label">Calories</span>
                 </div>
                 <div class="nutrition-item">
                   <span class="nutrition-value">{getNutrientValue(selectedRecipe.nutrition?.nutrients || [], 'Fat')}g</span>
                   <span class="nutrition-label">Fat</span>
                 </div>
                 <div class="nutrition-item">
                   <span class="nutrition-value">{getNutrientValue(selectedRecipe.nutrition?.nutrients || [], 'Carbohydrates')}g</span>
                   <span class="nutrition-label">Carbs</span>
                 </div>
                 <div class="nutrition-item">
                   <span class="nutrition-value">{getNutrientValue(selectedRecipe.nutrition?.nutrients || [], 'Protein')}g</span>
                   <span class="nutrition-label">Protein</span>
                 </div>
               </div>
             </div>
           </div>
           
           <div class="recipe-right">
             <div class="ingredients-section">
               <h2>Ingredients</h2>
               <ul class="ingredients-list">
                 {#each selectedRecipe.extendedIngredients as ing}
                   <li class="ingredient-item">
                     <span class="ingredient-measure">{ing.amount} {ing.unit}</span>
                     <span class="ingredient-name">{ing.name}</span>
                   </li>
                 {/each}
               </ul>
             </div>
             
             <div class="instructions-section">
               <h2>Instructions</h2>
               <div class="instructions-list">
                 {#if selectedRecipe.analyzedInstructions.length > 0}
                   {#each selectedRecipe.analyzedInstructions[0].steps as step}
                     <div class="instruction-step">
                       <div class="step-number">{step.number}</div>
                       <div class="step-text">{step.step}</div>
                     </div>
                   {/each}
                 {:else}
                   <p class="no-instructions">No detailed instructions available.</p>
                 {/if}
               </div>
             </div>
           </div>
         </div>
         
         <!-- Reviews Section with Rating -->
         <div class="reviews-section-detailed">
           <h2>Reviews</h2>
           
           {#if user && showReviewForm}
             <div class="add-review-form">
               <div class="rating-input">
                 <label class="rating-label">Your Rating:</label>
                 <div class="star-rating-input">
                   {#each [1, 2, 3, 4, 5] as star}
                     <button 
                       type="button"
                       class="star-btn {userRating >= star ? 'active' : ''}"
                       on:click={() => setRating(star)}
                     >
                       ★
                     </button>
                   {/each}
                 </div>
               </div>
               <textarea 
                 bind:value={userReview}
                 placeholder="Share your thoughts about this recipe..."
                 class="review-textarea"
               ></textarea>
               <div class="review-form-actions">
                 <button class="submit-review-btn" on:click={submitReviewWithRating}>
                   Submit Review
                 </button>
                 <button class="cancel-review-btn" on:click={() => showReviewForm = false}>
                   Cancel
                 </button>
               </div>
             </div>
           {/if}
           
           <!-- Display User's Reviews -->
           {#if userReviews.length > 0}
             <div class="user-reviews">
               <h3>Your Reviews</h3>
               {#each userReviews.filter(review => review.recipeId === selectedRecipe.id) as review}
                 <div class="review-item">
                   <div class="review-header">
                     <div class="review-rating">{renderStars(review.rating)}</div>
                     <span class="review-date">{new Date(review.createdAt).toLocaleDateString()}</span>
                   </div>
                   <p class="review-text">{review.review}</p>
                 </div>
               {/each}
             </div>
           {/if}
           
           <!-- Comments Section -->
           <Comments recipeId={selectedRecipe.id} {user} backendBase={BACKEND_BASE} />
         </div>
       </div>
     </div>
   </div>
 {/if}
</main>
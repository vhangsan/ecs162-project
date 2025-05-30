
<script lang="ts">
  import './app.css';
  import { onMount } from "svelte";

  let ingredients: string = "";
  let ingredientList: string[] = [];
  let recipes: any[] = [];
  let user: string | null = null;

  let showAccountSidebar = false;

  const BACKEND_BASE =
    import.meta.env.VITE_BACKEND_BASE || "http://localhost:8000";

  function login() {
    window.location.href = `${BACKEND_BASE}/login`;
  }

  function logout() {
    window.location.href = `${BACKEND_BASE}/logout`;
  }

  function addIngredient() {
    const trimmed = ingredients.trim();
    if (trimmed && !ingredientList.includes(trimmed)) {
      ingredientList.push(trimmed);
      ingredients = "";
    }
  }

  function removeIngredient(ing: string) {
    ingredientList = ingredientList.filter((i) => i !== ing);
  }

  async function searchRecipes() {
    try {
      const res = await fetch(
        `/recipes?ingredients=${encodeURIComponent(ingredients)}`
      );
      const recipeResults = await res.json();

      const enriched = await Promise.all(
        recipeResults.slice(0, 6).map(async (recipe: any) => {
          const nutritionRes = await fetch(
            `https://api.spoonacular.com/recipes/${recipe.id}/nutritionWidget.json?apiKey=c428e118a688421f85feba24422d004f`
          );
          const nutrition = await nutritionRes.json();
          return {
            ...recipe,
            calories: nutrition.calories || "N/A",
          };
        })
      );

      recipes = enriched;
    } catch (error) {
      console.error("Error fetching recipes or nutrition:", error);
    }
  }
</script>

<main>
  
  <header>
    <div class="grid_container">
      <div class="header">
        <p>Website Name</p>
      </div>
      <div class="header_icons">

    <div class="header-top">
      <div class="auth-controls">
        <img
          src="/home.svg"
          alt="Home"
          class="home-icon"
          on:click={login}
          title="Home"
        />
        {#if user}
          <div class="relative">
            <button
              class="text-sm font-medium underline"
              on:click={() => (showAccountSidebar = !showAccountSidebar)}
            >
              Account ▾
            </button>
            {#if showAccountSidebar}
              <div
                class="absolute right-0 bg-white border shadow p-2 mt-2 z-50"
              >
                <button on:click={logout} class="text-red-600 text-sm"
                  >Logout</button
                >
              </div>
            {/if}
          </div>
        {:else}
          <img
            src="/account.svg"
            alt="Login"
            class="login-icon"
            on:click={login}
            title="Login"
          />
        {/if}
        </div>
      </div>
    </div>
  </div>
  </header>







<div class="grid_container">
<div class="hero_image">
  <img src="/Hero_Image.png" alt="Hero Image" /> <!-- Hero Image -->
</div>
<div class="use_my_ingredients"><strong>USE MY INGREDIENTS</strong></div>
<div class="find_specific_recipe"><strong>FIND SPECIFIC RECIPE</strong></div>




<div class="search_bar"> <!-- Search Bar -->
    <div class="flex items-center justify-center min-h-[60vh]">
    <div class="relative w-full max-w-3xl">
      <input
        type="text"
        bind:value={ingredients}
        placeholder="Enter ingredients..."
        class="search_bar"
      />
    </div>
  </div>
</div>
<div class="search_buttons"> <!-- Search Buttons -->
  <button
    on:click={addIngredient}
    class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-700 text-xl"
      >
    🔍
  </button>
  <button
    on:click={searchRecipes}
    class="bg-green-600 text-white px-6 py-2 rounded block mx-auto mb-10"
  >
    Search Recipes
  </button>
</div>




<div class="student_favorite"> <!-- Containers for STUDENT FAVORITES -->
  <p><strong>STUDENT FAVORITES</strong></p>
</div>
  <div class="favorites_wrapper">
    <div class="student_favorite1"><img src="/Temp_Image.jpg"></div>
    <div class="student_favorite2"><img src="/Temp_Image.jpg"></div>
    <div class="student_favorite3"><img src="/Temp_Image.jpg"></div>
</div>
</div>








  <!-- <p class="text-center text-gray-500 text-lg mb-8">Turn waste into taste!</p> -->

  <!-- <div class="flex items-center justify-center min-h-[60vh]">    ORIGINAL SEARCH BAR
    <div class="relative w-full max-w-3xl">
      <input
        type="text"
        bind:value={ingredients}
        placeholder="Enter ingredients..."
        class="bg-purple-100 w-full pl-6 pr-12 py-5 rounded-full text-base focus:outline-none shadow-md"
      />
      <button
        on:click={addIngredient}
        class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-700 text-xl"
      >
        🔍
      </button>
    </div>
  </div> -->

  <div class="flex flex-wrap justify-center gap-3 mt-4 mb-8">
    {#each ingredientList as ing}
      <span
        class="bg-white border px-4 py-2 rounded-full flex items-center shadow-sm gap-2"
      >
        <span>{ing}</span>
        <button
          class="text-gray-500 hover:text-red-500"
          on:click={() => removeIngredient(ing)}>×</button
        >
      </span>
    {/each}
  </div>

  <!-- <button
    on:click={searchRecipes}
    class="bg-green-600 text-white px-6 py-2 rounded block mx-auto mb-10"
  >
    Search Recipes
  </button> -->
  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
    {#each recipes.slice(0, 6) as recipe}
      <div class="border rounded shadow p-4">
        <h3 class="font-bold text-lg">{recipe.title}</h3>
        <div class="text-sm text-gray-600 mt-1">
          Calories: {recipe.calories}
        </div>
        <img
          src={recipe.image}
          alt={recipe.title}
          class="w-full h-40 object-cover rounded mb-2"
        />
      </div>
    {/each}
  </div>
</main>

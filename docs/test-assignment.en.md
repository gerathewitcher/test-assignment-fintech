**Test Assignment: "Build a REST API Application"**

**Description.**  
Implement a **REST API** application for a directory of *Organizations*, *Buildings*, and *Activities*.

1. **Organization** - Represents an organization card in the directory and must include:
   * Name: e.g., LLC "Horns and Hooves"
   * Phone numbers: an organization can have multiple phone numbers (2-222-222, 3-333-333, 8-923-666-13-13)
   * Building: an organization must belong to one specific building (e.g., Blyukhera 32/1)
   * Activities: an organization can have multiple activity types (e.g., "Dairy products", "Meat products")
2. **Building** - Must contain at least:
   * Address: e.g., Moscow, Lenin St. 1, office 3
   * Geographic coordinates: latitude and longitude
3. **Activity** - Used to classify organization activity types in the catalog.  
   Has a name and supports a tree structure (nested activities). Example:

  - Food  
    - Meat products  
    - Dairy products  
  - Cars  
    - Trucks  
  - Passenger cars  
      - Spare parts  
      - Accessories
4. **Stack** - fastapi + pydantic + sqlalchemy + alembic

**Application functionality.**  
User interaction is done via **HTTP** requests to the **API server** using a **static API key**.  
All responses must be in **JSON** format. Implement the following methods:

* list all organizations located in a specific building
* list all organizations related to a specific activity type
* list organizations within a given radius/rectangular area relative to a map point; list buildings
* get organization details by organization identifier
* search organizations by activity type with subtree support.  
  Example: searching by "Food" (first level) must return organizations with activities "Food", "Meat products", "Dairy products"
* search organizations by name
* limit activity nesting depth to 3 levels

**Task requirements**

* Package the application into a Docker container so it can be deployed on any machine (add deployment instructions if needed)
* Add Swagger UI or Redoc documentation with descriptions of all application methods

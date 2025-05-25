# Airbus Analytics Web Application

Welcome to the **Airbus Analytics** web application! This README provides a comprehensive overview of the project, explains the purpose of each file and folder, and guides you through installation, usage, and customization.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features & Functionalities](#features--functionalities)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Running the Application](#running-the-application)
6. [Project Structure](#project-structure)
7. [File & Folder Breakdown](#file--folder-breakdown)
8. [Detailed Functionality Guide](#detailed-functionality-guide)
9. [Customization & Theming](#customization--theming)
10. [Deployment](#deployment)
11. [Contributing](#contributing)
12. [License](#license)

---

## Project Overview

The **Airbus Analytics** application is a lightweight, responsive web interface built with Flask, Bootstrap, and custom CSS. It enables stakeholders to:

* **Visualize** and **analyze** Airbus project data.
* Switch between light and dark themes for optimal readability.
* Access key modules such as project listings, detailed dashboards, and contact information.

The goal is to provide a polished, professional tool that matches Airbus’s brand identity and enhances user engagement through a clean UI.

## Features & Functionalities

* **Landing Page**: A welcoming dashboard summarizing core metrics.
* **Navigation Bar**: Responsive menu to access "Accueil", "Projets", and "Contact" sections.
* **Theme Toggle**: Light/dark mode switch for user comfort.
* **Animated Cards**: Smooth entry animations via Animate.css.
* **Modular Design**: Easily extendable templates and styles.

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

* **Python 3.7+**
* **pip** (Python package installer)
* **Git** (optional, for cloning the repository)

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/airbus-analytics.git
   cd airbus-analytics
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Set the Flask app environment variable**

   ```bash
   export FLASK_APP=app.py      # macOS/Linux
   set FLASK_APP=app.py         # Windows
   ```

2. **Launch the server**

   ```bash
   flask run
   ```

3. **Open in browser**
   Navigate to `http://127.0.0.1:5000` to view the application.

## Project Structure

```
airbus-analytics/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── theme-toggle.js
└── README.md
```

## File & Folder Breakdown

* **app.py**: Entry point of the Flask application. Defines routes and view functions.

* **requirements.txt**: Lists Python dependencies (Flask, etc.).

* **templates/index.html**: Main HTML template using Bootstrap layout and includes:

  * Metadata and viewport settings
  * Links to Bootstrap CSS, Animate.css, and `style.css`
  * Navbar with brand and navigation links
  * Theme toggle button (`data-theme` attribute)
  * Content container and animated card component
  * Footer section
  * Scripts for Bootstrap and theme toggle logic

* **static/css/style.css**: Custom styles defining:

  * **Typography**: Georgia serif for a professional look
  * **Color Variables**: Airline-inspired palette for light and dark modes
  * **Component Styling**: Shadows, border radii, and hover effects for navbar, cards, buttons, and footer

* **static/js/theme-toggle.js**: (Optional separate file) Contains JavaScript to switch `data-theme` between "light" and "dark", updating the toggle icon.

## Detailed Functionality Guide

### 1. Landing Page

* **Purpose**: Introduces users to Airbus Analytics with a prominent, animated card.
* **Usage**: View metrics or welcome message. This template can be extended to show live data or charts.

### 2. Navbar & Navigation

* **Components**:

  * Brand label: "Airbus Analytics"
  * Links: "Accueil", "Projets", "Contact"
  * Theme toggle: Click to switch modes (🌙/☀️)
* **Behavior**: Collapsible on smaller screens; remains fixed at top.

### 3. Theme Toggle

* **Goal**: Allow users to choose light or dark theme for readability.
* **Implementation**:

  1. HTML `<html data-theme="light">` default.
  2. CSS variables under `:root` and `[data-theme="dark"]` selectors.
  3. JS listens for button click, toggles the attribute and icon.

### 4. Animated Cards

* **Library**: Animate.css
* **Example**: `<div class="card animate__animated animate__fadeIn">`
* **Use Case**: Apply animations to new elements or dashboards for better user experience.

## How to Use the Application

1. **Upload Your Data**

   * On the **Accueil** page, click the **Upload** button to select your project data file (CSV, JSON, etc.).
   * After uploading, a confirmation message indicates successful import.
   * **Priority Flag**: In your Excel/CSV file, add a **Priority** column (`TRUE/FALSE` or `1/0`) for each project. The application will automatically highlight prioritized projects.

2. **Choose a Scenario**

   * Navigate to the **Projets** section in the navbar.
   * Select a scenario from the list or use the search bar to find a specific project.
   * Click **View Details** to load the dashboard for that scenario.
   * **Unchosen Projects**: Use the filter option to toggle viewing only projects not marked as priority.

3. **Interacting with the Dashboard**

   * **Metrics Overview**: Key indicators (progress, budget, timeline) appear in animated cards.
   * **Optimizing Curve**: A dynamic curve shows budget vs. outcome based on your data.

     * Drag the budget slider or input a value to see real-time curve updates.
   * **Goal Setting** (Optional): Enter a target KPI (e.g., weight reduction, cost savings).

     * The dashboard highlights on the curve where you need to allocate resources to meet your goal.
   * **Charts & Tables**: Scroll for interactive graphics and data tables.
   * **Filtering**: Use dropdowns to filter by date range, department, or other parameters.

4. **Downloading Reports**

   * Click the **Export** button to download a PDF or Excel report summarizing the selected scenario.
   * Reports include charts, tables, and key insights.

5. **Contact & Support**

   * Go to the **Contact** page and submit a support form if you encounter issues.
   * Our team will follow up with troubleshooting steps and guidance.

When you run the application after uploading your data and choosing a scenario, the dashboard presents real-time metrics, optimization curves, goal visualizations, and downloadable reports, empowering data-driven decisions for your Airbus projects.

## Customization & Theming

* **Fonts**: Change `font-family` in `style.css` to any system serif or imported font.
* **Colors**: Adjust CSS variables in `:root` for your brand colors.
* **Animations**: Add other Animate.css classes (e.g., `animate__zoomIn`) to elements.
* **Additional Pages**: Duplicate `index.html` as a base and update the content area for new routes.

## Contributing

Contributions are welcome! Please fork the repo, create a feature branch, and submit a pull request. Follow the existing code style and document new components.

---

Thank you for using **Airbus Analytics**! If you have any questions, please reach out to the development team.


int calculate_bonus(int base_salary) {
    // Example bonus calculation logic
    if (base_salary < 1000) {
        return base_salary * 0.1; // 10% bonus for low salaries
    } else if (base_salary < 5000) {
        return base_salary * 0.05; // 5% bonus for mid-range salaries
    } else {
        return base_salary * 0.02; // 2% bonus for high salaries
    }
}
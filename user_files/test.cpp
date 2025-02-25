#include <iostream>
using namespace std;
int main() {
int n = 25;
long long factorial = 1; // Use long long to avoid overflow for larger numbers
if (n < 0) {
cout << "Factorial is not defined for negative numbers." << endl;
} else {
for (int i = 1; i <= n; ++i) {
factorial *= i;
}
cout << "Factorial of " << n << " = " << factorial << endl;
}
return 0;
}
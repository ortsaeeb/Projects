#include "Matrix.h"

Matrix::Matrix()
{

for(int i=0;i<3;i++)// for the first matrix
{
    for(int j=0;j<3;j++)// for the second matrix
{

myArray[i][j]=(rand()%(20)); //random number generator to be inserted into both of the matrices
        }
    }
}

void Matrix::toString()
                        {
    for(int i=0;i<3;i++) //toString the first matrix
{
    for(int j=0;j<3;j++)//toString the second matrix 
{

cout<<myArray[i][j]<<" "; // printing out the Matrix
}

cout<<endl;
    }
}

Matrix Matrix::operator*(Matrix m1)
{

Matrix m;

int i,j,k,sum;

for(i=0;i<3;i++)// Iteration upto number of rows in the first Matrix
{
    for(j=0;j<3;j++)// Iteration upto number of columns in the second Matrix
{
sum=0;
    for(k=0;k<3;k++) // Iteration upto number of columns in the first Matrix
    sum=sum+myArray[i][k]*m1.myArray[k][j];// bring both matrices together for the multiplication 
    
{


}

m.myArray[i][j]=sum;
         }
    }

return m;
}
// I am not too sure how to do the equals method. can you go over that in class or in private?







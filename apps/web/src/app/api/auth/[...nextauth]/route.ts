import NextAuth, { NextAuthOptions } from "next-auth"
import CognitoProvider from "next-auth/providers/cognito"

const authOptions: NextAuthOptions = {
  providers: [
    CognitoProvider({
      clientId: process.env.COGNITO_CLIENT_ID || "",
      clientSecret: process.env.COGNITO_CLIENT_SECRET || "",
      issuer: process.env.COGNITO_ISSUER || "",
    }),
  ],
  secret: process.env.NEXTAUTH_SECRET || (process.env.NODE_ENV === "production" ? undefined : "dev-nextauth-secret-change-me"),
  session: {
    strategy: "jwt",
    maxAge: 8 * 60 * 60, // 8 hours (align with backend JWT)
    updateAge: 60 * 60,
  },
  jwt: {
    maxAge: 8 * 60 * 60,
  },
  cookies: {
    sessionToken: {
      name: process.env.NODE_ENV === "production" ? "__Secure-next-auth.session-token" : "next-auth.session-token",
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: process.env.NODE_ENV === "production",
      },
    },
  },
  callbacks: {
    async jwt({ token, account, profile }) {
      // Map Cognito roles and tenant info into the NextAuth token
      if (account && profile) {
        token.accessToken = account.access_token
        token.idToken = account.id_token
        token.role = (profile as any)["custom:role"] || "user"
        token.tenantId = (profile as any)["custom:tenant_id"] || ""
      }
      return token
    },
    async session({ session, token }) {
      // Inject token properties into the session for frontend access
      if (session.user) {
        (session as any).accessToken = token.accessToken;
        (session as any).role = token.role;
        (session as any).tenantId = token.tenantId;
      }
      return session
    }
  },
  pages: {
    signIn: '/auth/signin',
  },
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }

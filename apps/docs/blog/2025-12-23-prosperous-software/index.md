---
slug: prosperous-software
title: Prosperous Software Movement
description: "Bringing sustainable funding to public goods by revenue-sharing towards dependencies"
authors: [ryscheng]
tags: [featured, perspective, open-source]
---

_Bringing sustainable funding to public goods by revenue-sharing towards dependencies_

<!-- truncate -->

![prosperity-city](./prosperity-city.png)

The past 2 open source movements have yielded transformative effects to the software industry. The **Free Software Movement** led to the birth of Linux, GNU, and countless fundamental technologies that lie at the heart of nearly all modern computing systems. The later **Open Source Movement** led to an explosion of open source software in nearly every industry. Today, 99% of companies use free and open source (FOSS) software, and 70%+ of lines of code shipped to production comes from open source libraries \[[1](https://www.synopsys.com/software-integrity/resources/analyst-reports/open-source-security-risk-analysis.html#introMenu),[2](https://www.linuxfoundation.org/blog/blog/a-summary-of-census-ii-open-source-software-application-libraries-the-world-depends-on)\]. FOSS software is the bedrock of the entire economy, which has been growing exponentially with technology.

The predominant software licenses of today do not reflect the financial realities of the modern economy. Not only do FOSS developers rarely benefit from this incredible growth, many struggle to find support for their project. This common scenario applies even with many projects that form the fundamental infrastructure that made this economic growth possible \[[3](https://www.mend.io/blog/how-the-heartbleed-vulnerability-shaped-openssl/),[4](https://english.ncsc.nl/latest/weblog/weblog/2024/the-xz-factor-social-vulnerabilities-in-open-source-projects),[5](https://lwn.net/Articles/1034966/),[6](https://johncodes.com/archive/2023/04-22-revisiting-the-core-js-situation/),[7](https://www.theregister.com/2021/05/12/babel_money_woes/),[8](https://kennethreitz.org/essays/2023-01-an_overdue_apology)\]. Past open software movements focused on principles of freedom (e.g. GPL, AGPL) or open collaboration (e.g. Apache, MIT).

We propose that we need a new phase of software, called the **_Prosperous Software Movement_**, with the goal of enabling all the value creators in the economy to financially benefit from the prosperity they helped create. To meet this challenge, we believe there needs to be a new class of software licenses that rewards these developers, while holding true to the principles that make the open source community great. To further this social contract we are creating a new license, called the **_Public Prosperity License (PPLv1)_**.

At the heart of this proposal is the intention of **revenue-sharing**. The mechanism behind PPL is simple: if you use PPL-licensed software in your stack and you make over $X in annual revenue, you must share Y% of your revenue **back to your dependencies**.

We expect that not all companies will be willing to share in revenue or license their software in this way. However, we revenue-share for many reasons beyond gratitude and altruism. We believe that fairly compensating value creators and incentivizing more innovation at every layer of the technology stack will lead to an ecosystem of new digital products that collectively out-innovate the alternative group of uncooperative companies.

If you are an open source project and you share this intention, please [**sign up to join the working group**](https://pgf.ing/join) and engage in a dialogue to figure out how we can make this work for your organization. Anyone can join our Telegram group chat [**here**](https://pgf.ing/chat).

## Why is this important now?

Proponents of open source software have made many sound arguments on why we should fund digital public goods like free and open source software. It makes our software supply chain more secure, when developers have the resources to maintain and fix bugs \[[9](https://openssf.org/)\]. Open source software lowers the barrier to entry in a global digital market, facilitating better economic inclusion, especially in developing countries \[[10](https://cdn.sida.se/publications/files/sida3460en-open-source-in-developing-countries.pdf)\]. Lastly and most obviously, it is the right thing to do. You inevitably use open source software every day, either directly or indirectly in nearly every piece of software.

However as prosperous software is an economic proposal, we’ll focus on a forward-looking economic argument:

### Funding public goods will accelerate the economy

Free and open source software is digital public infrastructure, accessible to anyone on Earth with a computer. When we invest in better infrastructure, we bring step-changes to economic growth. Relying on donation platforms to fund public infrastructure is insufficient to bring the type of society–wide coordinated investment we need to make to build the future of technology. Nobody likes to pay tolls or taxes, but we cannot deny that the economy would look a lot smaller without the interstate highway system.

### The growing AI economy is the time to embody these changes

We are living in a unique moment in time, where the tech industry is actively re-imagining every layer of the stack, including:

- How data is stored and processed with new types of databases and storage systems optimized for AI
- How applications are architected with new AI application frameworks
- How users interact with machines via voice-control, brain-computer interfaces, and intelligence directly embedded into everyday devices

We are living through one of the most inventive moments in human history. As we displace the prior generation of software, we are building brand new open technology to realize this future. Now is the opportunity to embed new principles into our collective development stack, which is already dominated by open source software.

## Design Goals

To ground the principles of this new software movement, we suggest the following goals:

### Feed the “Collaboration Monster” 🪴🫶

People love free and open source software because it enables unrestricted collaboration. Anyone can [run, study, modify, and redistribute](https://www.gnu.org/philosophy/free-sw.en.html) the software, without asking for permission from the software authors. This is in contrast to commercial licenses or source-available licenses (like [BSL](https://mariadb.com/bsl-faq-mariadb/)), where users must ask for permission to run or modify the software in commercial settings. Prosperous software follows in the spirit of free and open source. Anyone in the world, from students to professional software developers should be able to freely use, fork, contribute, and even sell prosperous software without negotiating with software authors, as long as they follow well-specified requirements (i.e. revenue-sharing to approved mechanisms).

### Collective bargaining 👪

Individuals and companies can and often do pledge to donate to open source \[[11](https://opensourcepledge.com/)\] without the need for a new license. However, “prosperous licenses” could form the basis of a new form of collective bargaining among the software authors. As more projects choose prosperous software licenses, it grows the movement’s collective bargaining power in positive-sum ways. Companies that build within the revenue-sharing ecosystem benefit from the accelerationist effects of a growing corpus of open technology. Companies that build software outside of this ecosystem must do so at the cost of reduced velocity.

### No self-dealing ❌🔄

Revenue-sharing should benefit individuals and organizations outside of the donor’s control. If a donor could simply benefit themselves from direct or indirect transactions, it would run counter to the intention of revenue-sharing with other public goods. We can draw inspiration from existing legal language around [self-dealing](<https://www.law.cornell.edu/cfr/text/26/53.4941(d)-1>).

### Wide compatibility with various software licenses and business models 🏞️

PPL should be compatible with a wide variety of software licenses, from commercial proprietary software to free GPL software. Similarly, these licenses should be compatible with a wide variety of business models, use cases, and deployment models. The intention is not to coerce other software developers to adopt the same license. Rather, PPL software simply adds a revenue-sharing requirement to its users. Being able to easily dual-license with PPL would greatly benefit adoption.

### Enforceable 🤝

While PPL does not coerce any software developers to use the license, if companies do use PPL-licensed software, we must have the legal framework to enforce compliance in domestic and international courts. The legal theory should be sound, yet compatible with the ethos of the free and open source community.

## How will PPL work?

![flow-diagram](./flow-diagram.png)

### Revenue-sharing to the prosperous software community

1. A developer chooses to license their software with PPL (e.g. Library-Foo)
   - PPL contains a **“profit-left”** clause, which creates a revenue-sharing obligation for any users of the software.
   - The developer chooses the revenue-sharing percentage. For example: PPL-1% or PPL-5%.
2. An engineer at a tech company, Startup-Bar, uses Library-Foo to build a commercial service.
3. While Startup-Bar is young and unprofitable, there are no obligations. They use PPL-licensed software freely as they would any open source software, allowing them to focus on growth and product development.
4. When Startup-Bar hits certain revenue thresholds, the revenue-sharing clause kicks in.
5. Startup-Bar has a deadline (e.g. 1 calendar year) to **donate to an approved dependency funding mechanism**.
6. If anyone forks Library-Foo, they must inherit the PPL profit-left clauses in the fork.
7. If a company uses 2 pieces of PPL-software, we aggregate their revenue-sharing percentages.  
   _Note: we are still deciding if it should be MIN(), MAX(), AVG(), or MEDIAN(). For example, MAX(PPL-5%, PPL-1%) \= 5% revenue-sharing_

### Prosperous software governance

In order to organize the movement and form a base of advocacy, we plan to form a membership-based non-profit.

#### Defining a charter and brand

Similar to the role that the [Free Software Foundation](https://www.fsf.org/) served for the free software movement, or the [Open Source Initiative](https://opensource.org/) for the open source movement, this governing body will define the movement’s charter and rules of engagement. One of the first documents will be a “Prosperous Software Definition”.

#### Steward approval of prosperous software licenses

While PPL may be one of the first licenses, we do not expect it to be the only license. This governing body will provide clear guidelines and principles that enable license innovation to grow the movement in positive-sum ways. Developers will need a menu of options to satisfy their specific use case. While building on existing open source principles, giving anyone the unrestricted ability to view, run, modify, and redistribute software, approved software licenses should include **profit-left** clauses to give back to the movement.

#### Approve and audit dependency funding mechanisms

In the past couple decades, the public goods funding ecosystem has made important strides in innovating on a menu of options for providing financial support. As a brief summary of the different categories:

1. **Donation platforms**  
   (e.g. [GitHub sponsors](https://github.com/open-source/sponsors), [Open Collective](https://opencollective.com/), [Drips](https://www.drips.network/), [Ecosystem Funds](https://funds.ecosyste.ms/))  
   These platforms provide the most flexibility to donors in choosing how they fund their dependencies. The governing body will need to work with each platform to ensure that donors send funds only to eligible projects and do not self-deal.
2. **Algorithmic dependency funding**  
   (e.g. [thanks.dev](https://thanks.dev/home), [Deepfunding](https://www.deepfunding.org/), [Retrofunding](https://atlas.optimism.io/))  
   Algorithmic dependency funding makes it significantly easier to divide funds fairly across all of your dependencies. Modern applications can incorporate hundreds or thousands of dependencies. Similarly, the governing body will need to audit these mechanisms to ensure only proper flows are allowed.
3. **Foundations**  
   (e.g. [Linux Foundation](https://www.linuxfoundation.org/), [Apache Foundation](https://apache.org/))  
   The governing body may also approve other non-profits to receive funds directly, relying on their internal governance to make proper use of funds.

In choosing allowed funding mechanisms, the governing body should at least consider the following questions:

- Does the mechanism provide sufficient guardrails to prevent or minimize the risk of self-dealing?
- Does the mechanism take measures to ensure that funding benefits the future growth of prosperous software with approved licenses?
- Does the mechanism make it substantially easy for donors to tap into existing revenue (e.g. transaction fees, yield, etc)?

The governing body should also research and support new funding mechanisms that can better solve these problems at scale.

#### Advocacy and Enforcement

The governing body should help prosperous software projects monitor compliance and enforce the terms of the license. We should be adequately prepared for legal enforcement, but legal enforcement should only be applied only in the worst case scenario. In the common case, the governing body should help the movement grow both social influence and technical mechanisms. We should build revenue sharing payment channels directly into the distributed systems that process transaction fees. We should build a social movement that influences organizations to join these revenue-sharing networks pre-emptively.

#### Membership benefits and support

Joining the prosperous software movement requires opt-in from software developers to succeed. The governing body should provide legal and administrative support to help developers re-license. The body can produce educational materials and events to grow the community. The governing body should also organize other positive-sum benefits to joining as a member, such as patent-pooling.

## Public Prosperity License Adoption

### Why should developers license using PPL?

Today, developers are left with a false choice between 2 major classes of licenses: open source licenses and commercial licenses.

|                                                 | Open Source | Proprietary | Source-available | Prosperous |
| :---------------------------------------------- | :---------- | :---------- | :--------------- | :--------- |
| Freedom to study                                | ✅          | ❌          | ✅               | ✅         |
| Freedom to run                                  | ✅          | ❌          | ❌               | ✅         |
| Freedom to modify                               | ✅          | ❌          | ❌               | ✅         |
| Freedom to redistribute                         | ✅          | ❌          | ❌               | ✅         |
| Developers paid                                 | ❌          | ✅          | ✅               | ✅         |
| Does not require negotiation for production use | ✅          | ❌          | ❌               | ✅         |

#### Compared to existing open source license (e.g. Apache, MIT, BSD)?

Existing open source licenses provide an unrestricted ability to [run, study, modify, and redistribute](https://www.gnu.org/philosophy/free-sw.en.html#four-freedoms) the software. The [OSI definition](https://opensource.org/osd) explicitly prevents any restrictions on groups of people, fields of endeavor, or distribution method. These licenses maximally feed the collaboration monster, giving anyone the right to do whatever they want with the software. Open source software cannot restrict commercial use or competition.

Because these licenses do not include any financial commitments, developers are left trying to monetize via auxiliary methods around the open core software, offering consulting, support, or selling related proprietary services. While these business models may work for some software, there are often no clear auxiliary monetization models for many pieces of critical software. We believe that when people build useful software, they should be rewarded for their contributions to society.

#### Compared to a commercial or source-available license (e.g. BSL, FSL)?

A growing number of developers are instead choosing a commercial license, which closes off at least one of the fundamental freedoms of free software. Certain licenses explicitly forbid competitive commercial services \[[12](https://prosperitylicense.com/versions/3.0.0), [13](https://faircode.io/), [14](https://osaasy.dev/)\]. Other licenses create similar restrictions with a time limit \[[15](https://mariadb.com/bsl-faq-mariadb/), [16](https://fsl.software/)\]. For example, BSL prevents production uses before a “change date”, after which the software converts to an open source license.

By chipping away at the four freedoms of free software, we end up in a gray area between fully closed proprietary software and free software. These restrictions slow the pace of innovation. In the best case scenario, software developers must negotiate bilateral agreements with each piece of software they use. In the worst case, developers are barred from using or building on top of existing work.

#### PPL: A third pathway for maximal collaboration with financial sustainability built-in

The four freedoms to run, study, modify, and redistribute are precisely why people love the free software movement. These freedoms enable unrestricted collaboration in a global marketplace. This unrestricted ability to collaborate is precisely why in many domains, open technologies have consistently out-innovated their proprietary counterparts.

With PPL, we want to preserve this unrestricted collaboration without requiring developers to negotiate individual permissioned uses. Developers can do anything they want, including sell a competitive service. Much like copyleft clauses, profit-left clauses simply state an additional obligation of any user of the software: users must revenue-share with their dependencies using approved mechanisms. The clause should be clear and unambiguous, allowing for users to pay after achieving financial success, without pre-emptive negotiations.

### Dissecting different types of developers

Developers will have very different incentives for adoption, depending on where their software sits in the technology stack and which industry they serve. We should provide tailored adoption guidance for these different types of developers to ease the transition.

#### Open source libraries

These developers have some of the strongest incentives to license with PPL. Libraries often have very limited alternative monetization strategies. Hopefully these developers identify with the mission and purpose of prosperous software. As more developers choose to license their software PPL, it increases both the bargaining power of the coalition, as well as the surface area of software that would be subject to revenue-sharing. PPL may be one of the strongest pathways to pushing users to financially support these dependencies with recurring revenue streams.

#### Open source platforms and services

Open source platforms, like operating systems, cloud platforms, and blockchains often have direct methods of monetizing their service. This class of software typically has an open core company behind them. In the case where the company wants many deployments, the revenue-sharing percentage can be set accordingly to reflect the existing commercial expectations. For example, many Ethereum layer 2 networks like Optimism already try to impose a [revenue-share](https://docs.optimism.io/superchain/superchain-information/superchain-revenue-explainer) among chain deployments. PPL empowers these platforms with a legal mechanism to enforce revenue sharing.

On the other end of the spectrum, the company may prefer to have only one canonical deployment of the service. In this case, dual licensing PPL with a high revenue-sharing percentage provides an even stronger barrier than AGPL, which can be easily [circumvented](https://opensource.stackexchange.com/questions/8025/difference-between-mongodb-sspl-and-gnu-agpl). The dual PPL/commercial license would require revenue-sharing in the default case, with exceptions granted to companies that negotiate a commercial license.

### Why join as a founding member?

The initial founding members will have outsized governance power in the beginning. We expect the initial set of dependency funding mechanisms and approved licenses to be a much narrower set in the beginning. As such, initial revenue flows will be largely influenced by the decisions made by the founding membership.

### Why consume PPL software?

#### Non-commercial consumers of PPL software

Non-commercial users of PPL software, from hobbyists to academics would be unaffected by the revenue-sharing requirements. They freely use prosperous software just like any open source software.

#### Commercial consumers of PPL software

Corporations are highly rational organizations. As long as the revenue-sharing costs are less than the switching costs to an alternative, they will continue to use it. This calculus will depend on what software component we are considering. For example if there are many non-PPL open source alternatives (as in SQL databases), then there may be an incentive to avoid the PPL software. If there are no open source alternatives, but many commercial alternatives, it will depend on the market pricing power of this class of software. On the other end of the spectrum, if there are no alternatives, then we would need to estimate the cost of the enterprise to build their own version from scratch. We expect companies to make the rational decision to continue using PPL-licensed software, as long as the cost is lower than the switching costs. As the corpus of PPL-licensed software grows, it gives the PPL community the ability to charge higher revenue-sharing percentages.

## Conclusion

We are reaching a breaking point among many open source developers. Great software developers want to write useful open software and get paid fairly for it when it is used. We want to continue writing software with the freedoms and principles that make free and open source software great. In order to do so, we need to evolve past licenses that were written for a past era. Digital software is undeniably a foundational component of nearly every corner of the economy, and we need sustainable mechanisms to fund it.

This won’t be for everyone. It is up to us to show that new software built in this open model will out-innovate, out-compete, and eventually out-grow the alternative closed counterparts, like the free software movement did with Linux and the operating system market. Unlike the free and open source movements, this one will be juiced with the financial resources to thrive.

- If you’re an open source project that is interested, please join our working group and let’s figure out how to make this work for you.  
  [https://pgf.ing/join](https://pgf.ing/join)
- If you’re a lawyer with experience writing software licenses, please reach out to me directly  
  [https://www.raymondcheng.net/](https://www.raymondcheng.net/)
- If you’re a public goods or open source advocate, please join us on the group chat to help us organize, evangelize, and strategize.  
  [https://pgf.ing/chat](https://pgf.ing/chat)

## FAQ

This post is just the beginning of a long journey towards building a PPL movement. There remain many open questions we will need to decide as a community, before launching. In this section, I’ll raise some questions and offer some suggestions, but expect these answers to change as the community engages in deeper discussion:

**How much should we charge in the revenue-sharing requirement?**  
We could consider 2 approaches:  
The first is to follow a well-known comparable, like the Epic games ecosystem

- Free for any use case under $1M in revenue
- Once you reach \>$1M in revenue, pay 5% towards your prosperous software dependencies

The second approach is to pick a trivially small revenue-sharing percentage (i.e. 1 bps) to grow the movement’s membership and begin the social practice of funding dependencies. We leave this for discussion among the initial founding membership.

**Do PPL-licensed projects need to also revenue-share?**  
Yes. If PPL-licensed projects receive revenue from this arrangement, we expect these projects to also pay their own dependencies as well, creating a network of funding. This enables developers at every layer of the stack to benefit from the movement’s cash infusion, not just front-line software tools and libraries.

There is one key exception to this. For projects that dual license with PPL and do not have any PPL-licensed software in their dependency tree, then there is a pathway with no profit-left obligations.

**Why revenue? Why not profits?**  
Tech companies are famously unprofitable. Many companies that are market-dominant or traded in public markets choose to stay unprofitable to fuel growth and expansion. Revenue is one of the best indicators of traction and business maturity.

**Why revenue? Why not seats or a percentage of existing expenses?**  
We would like to avoid introducing any loopholes or perverse incentives. Revenue is the simplest and clearest way to measure value exchange in any industry.

**Is there a free-rider problem?**  
To be eligible for funding, prosperous software must be licensed with an approved license with an appropriate profit-left clause. This ensures that we appropriately reward the developers who help make this movement succeed.

**Is profit-left considered a royalty or fee?**  
[Royalties](https://www.law.cornell.edu/wex/royalty) are defined as “compensation to the owner of intellectual property for the right to use or profit from the property”. The profit-left clause is not meant to incur economic exclusion, and everyone is pre-emptively granted the right to use the software for any purpose. Rather, it imposes an ex post facto obligation to donate to dependencies that is always a fraction of the value generated.

**Is this considered open source?**  
There are a number of institutions that manage approval processes for free and open source software. In fact, many [disagree with each other](https://en.wikipedia.org/wiki/Comparison_of_free_and_open-source_software_licenses#approvals) on whether specific licenses qualify. We have not yet applied to any approval process, but it may be safer to just avoid calling prosperous software, “open source software”. We have highly overlapping, but different goals.

**Why cash donations?**  
Many tech companies will donate resources, like CI compute hours or developer time. Regardless of intention, this often gives the corporation power and influence over the project. Cash is the ultimate unburdened resource, giving the software maintainer the freedom to allocate resources towards their most pressing needs. We would never expect companies to accept payment for commercial products in the form of volunteer time.

**How do we make sure that this new governing body stays true to its principles?**  
Non-profit governance is a challenging topic with prominent incidents where foundations veer from their founding principles. We should engage with legal and governance experts to make sure we can avoid attempts to route around our founding principles.

**What revenues are subject to the revenue-sharing requirement?**  
Many big tech companies have many independent products with independent P\&L. We should limit the revenue-sharing component to the products and services that leverage the PPL software, rather than the revenue of the whole corporation.

**Who decides the revenue-sharing percentage requirements in the license?**  
As mentioned above, the bargaining power of any particular piece of software will depend on the market they operate in. As such, we suggest giving the PPL developer the freedom to choose the revenue-sharing percentage. We hope to provide high-level industry guidance, support, and defaults so that developers are not overwhelmed by the choice.

**What about using the PPL license for data and content?**  
In the AI economy, thinking about how we license data and information is as important as how we license software. Consider the case where an AI lab trains a coding LLM model on PPL software. In this case, we suggest that the revenue-sharing requirements should also apply to the LLM model. Similarly, we can imagine licensing books, articles, and data as PPL.

**What about a membership model with additional benefits?**  
Yes\! Copyright is only one form of intellectual property. We hope that the governing body can be a central point to organize patent pools, shared trademarks, and other forms of shared power.

**What if companies ban using PPL?**  
We should create the technical mechanisms to make fulfilling revenue-sharing obligations as simple as entering a credit card. Unlike GPL/AGPL, which some companies think of as an infinite cost, PPL has well-defined fractional financial costs. We hope companies will make the rational decision, as long as these costs are comparable to alternatives.

**Which software projects are qualified recipients?**  
To make it easy, clear, and unambiguous, we suggest donors can fund any software project that is licensed with a license approved by our tentative prosperous governing body, which will review licenses to meet the Prosperous Software Definition.

**How do we update the revenue-sharing percentage?**  
We should provide clear guidelines and support for projects to relicense their project. As markets evolve, projects may choose to re-license towards higher or lower revenue-sharing percentages.

**Are non-profit or governments exempt?**  
To make things simpler, we are not expecting any use case exceptions. Most organizations have a profit-and-loss statement that can be audited to determine amounts due.

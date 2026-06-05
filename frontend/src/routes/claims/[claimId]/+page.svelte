<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import {
		getClaimById,
		formatCurrency,
		formatDate,
		getStatusBadgeClass,
		type WarrantyClaim
	} from '$lib/api';

	let claim: WarrantyClaim | null = null;
	let loading = true;
	let error = '';

	$: claimId = $page.params.claimId;

	onMount(async () => {
		await loadClaim();
	});

	async function loadClaim() {
		loading = true;
		error = '';

		try {
			claim = await getClaimById(claimId);
		} catch (err: any) {
			error = err.response?.data?.detail || err.message || 'Failed to load claim';
			console.error('Load claim error:', err);
		} finally {
			loading = false;
		}
	}

	function formatDateTime(dateString: string): string {
		return new Date(dateString).toLocaleString('en-MY', {
			day: '2-digit',
			month: '2-digit',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<svelte:head>
	<title>{claim?.claimId || 'Claim'} - OEMPartner Dealer Portal</title>
</svelte:head>

{#if loading}
	<div class="loading-container">
		<div class="loading-spinner">
			<svg class="animate-spin" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				/>
			</svg>
			<p>Loading claim details...</p>
		</div>
	</div>
{:else if error}
	<div class="error-container">
		<div class="error-icon">
			<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
		</div>
		<h2>Claim Not Found</h2>
		<p>{error}</p>
		<a href="/claims" class="back-button">
			<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
			</svg>
			Back to Claims
		</a>
	</div>
{:else if claim}
	<div class="claim-detail">
		<!-- Top Navigation Bar -->
		<div class="top-nav">
			<a href="/claims" class="back-link">
				<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
				</svg>
				Back to Warranty Claims
			</a>
			<nav class="breadcrumb">
				<a href="/claims">Claims</a>
				<svg class="separator" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
				<a href="/claims?status={encodeURIComponent(claim.status)}">{claim.status}</a>
			<svg class="separator" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
			</svg>
			<span class="current">{claim.claimId}</span>
		</nav>
		</div>

		<!-- Claim Header -->
		<header class="claim-header">
			<div class="header-content">
				<div class="page-icon" class:breached={claim.sla.slaBreached}>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
				</div>
				<div class="header-text">
					<div class="claim-id-row">
						<span class="claim-id">{claim.claimId}</span>
						{#if claim.sla.slaBreached}
							<span class="sla-badge breached">
								<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
								SLA Breached
							</span>
						{/if}
					</div>
					<h1>{claim.vehicle.modelName}</h1>
					<div class="meta-row">
						<span class="dealer">{claim.dealer.name}</span>
						<span class="dot">•</span>
						<span class="date">Submitted {formatDate(claim.submittedAt)}</span>
					</div>
				</div>
			</div>
			<div class="header-status">
				<span class="badge {getStatusBadgeClass(claim.status)} status-badge">
					{claim.status}
				</span>
			</div>
		</header>

		<div class="content-grid">
			<!-- Sidebar (Left) -->
			<aside class="sidebar">
				<!-- Claim Summary -->
				<div class="sidebar-card summary-card animate-in" style="animation-delay: 0ms">
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
						</svg>
						<h3>Claim Summary</h3>
					</div>
					<div class="card-body">
						<div class="summary-row">
							<span class="label">Parts</span>
							<span class="value">{formatCurrency(claim.totals.partsTotal)}</span>
						</div>
						<div class="summary-row">
							<span class="label">Labour</span>
							<span class="value">{formatCurrency(claim.totals.labourTotal)}</span>
						</div>
						<div class="divider"></div>
						<div class="summary-row total">
							<span class="label">Total Claimed</span>
							<span class="value">{formatCurrency(claim.totals.claimTotal)}</span>
						</div>
						{#if claim.totals.approvedTotal > 0}
							<div class="summary-row approved">
								<span class="label">Approved Amount</span>
								<span class="value">{formatCurrency(claim.totals.approvedTotal)}</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Customer Info -->
				<div class="sidebar-card animate-in" style="animation-delay: 50ms">
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
						</svg>
						<h3>Customer</h3>
					</div>
					<div class="card-body">
						<div class="customer-name">{claim.customer.name}</div>
						<div class="contact-row">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
							</svg>
							<span>{claim.customer.phone}</span>
						</div>
						<div class="contact-row">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
							</svg>
							<span>{claim.customer.email}</span>
						</div>
						<div class="address">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
							<span>{claim.customer.address}</span>
						</div>
					</div>
				</div>

				<!-- Dealer Info -->
				<div class="sidebar-card animate-in" style="animation-delay: 100ms">
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
						</svg>
						<h3>Dealer</h3>
					</div>
					<div class="card-body">
						<div class="dealer-name">{claim.dealer.name}</div>
						<div class="dealer-info">
							<span class="dealer-code">{claim.dealer.dealerCode}</span>
							<span class="dealer-region">{claim.dealer.region}</span>
						</div>
					</div>
				</div>

				<!-- SLA Tracking -->
				<div class="sidebar-card sla-card animate-in" style="animation-delay: 150ms" class:breached={claim.sla.slaBreached}>
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<h3>SLA Tracking</h3>
					</div>
					<div class="card-body">
						<div class="sla-progress">
							<div class="progress-bar">
								<div 
									class="progress-fill" 
									class:warning={claim.sla.daysElapsed > claim.sla.targetDays * 0.7}
									class:danger={claim.sla.slaBreached}
									style="width: {Math.min(100, (claim.sla.daysElapsed / claim.sla.targetDays) * 100)}%"
								></div>
							</div>
							<div class="progress-labels">
								<span>0</span>
								<span class="target">{claim.sla.targetDays} days target</span>
							</div>
						</div>
						<div class="sla-stat">
							<span class="stat-value" class:danger={claim.sla.slaBreached}>{claim.sla.daysElapsed}</span>
							<span class="stat-label">days elapsed</span>
						</div>
						<div class="sla-row">
							<span class="label">Due Date</span>
							<span class="value">{formatDate(claim.sla.dueDate)}</span>
						</div>
						{#if claim.sla.slaBreached}
							<div class="sla-alert">
								<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
								</svg>
								<span>SLA has been breached by {claim.sla.daysElapsed - claim.sla.targetDays} days</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Review Info -->
				{#if claim.review}
					<div class="sidebar-card review-card animate-in" style="animation-delay: 200ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<h3>Review</h3>
						</div>
						<div class="card-body">
							<div class="review-decision" class:approved={claim.review.decision === 'Approved'} class:rejected={claim.review.decision !== 'Approved'}>
								{claim.review.decision}
							</div>
							<div class="review-row">
								<span class="label">Reviewed By</span>
								<span class="value">{claim.review.reviewedBy}</span>
							</div>
							<div class="review-row">
								<span class="label">Date</span>
								<span class="value">{formatDate(claim.review.reviewedAt)}</span>
							</div>
							{#if claim.review.rejectionReason}
								<div class="rejection-reason">
									<span class="label">Rejection Reason</span>
									<p>{claim.review.rejectionReason}</p>
								</div>
							{/if}
							{#if claim.review.comments}
								<div class="review-comments">
									<span class="label">Comments</span>
									<p>{claim.review.comments}</p>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Payment Info -->
				{#if claim.payment}
					<div class="sidebar-card payment-card animate-in" style="animation-delay: 250ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
							</svg>
							<h3>Payment</h3>
						</div>
						<div class="card-body">
							<div class="payment-amount">{formatCurrency(claim.payment.paymentAmount)}</div>
							<div class="payment-row">
								<span class="label">Date</span>
								<span class="value">{formatDate(claim.payment.paymentDate)}</span>
							</div>
							<div class="payment-row">
								<span class="label">Reference</span>
								<span class="value mono">{claim.payment.paymentReference}</span>
							</div>
							<div class="payment-row">
								<span class="label">Method</span>
								<span class="value">{claim.payment.paymentMethod}</span>
							</div>
						</div>
					</div>
				{/if}
			</aside>

			<!-- Main Content (Right) -->
			<div class="main-content">
				<!-- Vehicle Information -->
				<div class="detail-card animate-in" style="animation-delay: 0ms">
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
						</svg>
						<h2>Vehicle Information</h2>
					</div>
					<div class="card-body">
						<div class="info-grid">
							<div class="info-item span-2">
								<span class="label">Model</span>
								<span class="value highlight">
									{claim.vehicle.modelName}
									<span class="code">({claim.vehicle.modelCode})</span>
								</span>
							</div>
							<div class="info-item">
								<span class="label">Registration Number</span>
								<span class="value mono">{claim.vehicle.registrationNumber}</span>
							</div>
							<div class="info-item">
								<span class="label">Mileage at Claim</span>
								<span class="value">{claim.vehicle.mileageAtClaim.toLocaleString()} km</span>
							</div>
							<div class="info-item">
								<span class="label">Engine Number</span>
								<span class="value mono small">{claim.vehicle.engineNumber}</span>
							</div>
							<div class="info-item">
								<span class="label">Frame Number</span>
								<span class="value mono small">{claim.vehicle.frameNumber}</span>
							</div>
							<div class="info-item">
								<span class="label">Purchase Date</span>
								<span class="value">{formatDate(claim.vehicle.purchaseDate)}</span>
							</div>
							<div class="info-item">
								<span class="label">Warranty Period</span>
								<span class="value">{formatDate(claim.vehicle.warrantyStartDate)} – {formatDate(claim.vehicle.warrantyEndDate)}</span>
							</div>
						</div>
					</div>
				</div>

				<!-- Failure Details -->
				<div class="detail-card animate-in" style="animation-delay: 50ms">
					<div class="card-header failure">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
						</svg>
						<h2>Failure Details</h2>
						<span class="category-badge">{claim.failure.category}</span>
					</div>
					<div class="card-body">
						<div class="failure-description">
							<p>{claim.failure.description}</p>
						</div>
						{#if claim.failure.technicianNotes}
							<div class="technician-notes">
								<div class="notes-header">
									<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
									</svg>
									<span>Technician Notes</span>
								</div>
								<p>{claim.failure.technicianNotes}</p>
							</div>
						{/if}
						<div class="reported-date">
							<span class="label">Date Reported:</span>
							<span class="value">{formatDate(claim.failure.dateReported)}</span>
						</div>
					</div>
				</div>

				<!-- Parts Claimed -->
				{#if claim.partsClaimed && claim.partsClaimed.length > 0}
					<div class="detail-card animate-in" style="animation-delay: 100ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
							</svg>
							<h2>Parts Claimed</h2>
							<span class="count-badge">{claim.partsClaimed.length} items</span>
						</div>
						<div class="card-body no-padding">
							<div class="table-wrapper">
								<table class="detail-table">
									<thead>
										<tr>
											<th>Part</th>
											<th class="center">Qty</th>
											<th class="right">Unit Price</th>
											<th class="right">Total</th>
											<th class="center">Status</th>
										</tr>
									</thead>
									<tbody>
										{#each claim.partsClaimed as part}
											<tr>
												<td>
													<a href="/products/{part.partNumber}" class="part-link">
														{part.partNumber}
													</a>
													<span class="part-name">{part.partName}</span>
												</td>
												<td class="center">{part.quantity}</td>
												<td class="right">{formatCurrency(part.unitPrice)}</td>
												<td class="right font-semibold">{formatCurrency(part.totalPrice)}</td>
												<td class="center">
													{#if part.warrantyApproved}
														<span class="approval-badge approved">
															<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
															</svg>
															Approved
														</span>
													{:else}
														<span class="approval-badge pending">
															<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
															</svg>
															Pending
														</span>
													{/if}
												</td>
											</tr>
										{/each}
									</tbody>
									<tfoot>
										<tr>
											<td colspan="3" class="right">Parts Total:</td>
											<td class="right total">{formatCurrency(claim.totals.partsTotal)}</td>
											<td></td>
										</tr>
									</tfoot>
								</table>
							</div>
						</div>
					</div>
				{/if}

				<!-- Labour Claimed -->
				{#if claim.labourClaimed && claim.labourClaimed.length > 0}
					<div class="detail-card animate-in" style="animation-delay: 150ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<h2>Labour Claimed</h2>
							<span class="count-badge">{claim.labourClaimed.length} items</span>
						</div>
						<div class="card-body no-padding">
							<div class="table-wrapper">
								<table class="detail-table">
									<thead>
										<tr>
											<th>Operation</th>
											<th class="center">Hours</th>
											<th class="right">Rate</th>
											<th class="right">Total</th>
											<th class="center">Status</th>
										</tr>
									</thead>
									<tbody>
										{#each claim.labourClaimed as labour}
											<tr>
												<td>
													<span class="operation-code">{labour.operationCode}</span>
													<span class="operation-desc">{labour.description}</span>
												</td>
												<td class="center">{labour.hours}</td>
												<td class="right">{formatCurrency(labour.rate)}/hr</td>
												<td class="right font-semibold">{formatCurrency(labour.totalPrice)}</td>
												<td class="center">
													{#if labour.warrantyApproved}
														<span class="approval-badge approved">
															<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
															</svg>
															Approved
														</span>
													{:else}
														<span class="approval-badge pending">
															<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
															</svg>
															Pending
														</span>
													{/if}
												</td>
											</tr>
										{/each}
									</tbody>
									<tfoot>
										<tr>
											<td colspan="3" class="right">Labour Total:</td>
											<td class="right total">{formatCurrency(claim.totals.labourTotal)}</td>
											<td></td>
										</tr>
									</tfoot>
								</table>
							</div>
						</div>
					</div>
				{/if}

				<!-- Status History / Timeline -->
				<div class="detail-card animate-in" style="animation-delay: 200ms">
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
						</svg>
						<h2>Status History</h2>
					</div>
					<div class="card-body">
						<div class="timeline">
							{#each claim.statusHistory as entry, i}
								<div class="timeline-item" class:first={i === 0}>
									<div class="timeline-marker">
										<div class="marker-dot"></div>
										{#if i !== claim.statusHistory.length - 1}
											<div class="marker-line"></div>
										{/if}
									</div>
									<div class="timeline-content">
										<div class="timeline-header">
											<span class="status-name">{entry.status}</span>
											<span class="timeline-date">{formatDateTime(entry.changedAt)}</span>
										</div>
										{#if entry.notes}
											<p class="timeline-notes">{entry.notes}</p>
										{/if}
										<span class="changed-by">by {entry.changedBy}</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Back Link -->
		<div class="back-section">
			<a href="/claims" class="back-link">
				<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
				</svg>
				Back to Warranty Claims
			</a>
		</div>
	</div>
{/if}

<style>
	/* Animation */
	@keyframes fadeInUp {
		from {
			opacity: 0;
			transform: translateY(12px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.animate-in {
		animation: fadeInUp 0.4s ease-out both;
	}

	/* Loading State */
	.loading-container {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 400px;
	}

	.loading-spinner {
		text-align: center;
	}

	.loading-spinner svg {
		width: 3rem;
		height: 3rem;
		color: #0033A0;
		margin: 0 auto;
	}

	.loading-spinner p {
		margin-top: 1rem;
		color: #64748b;
		font-size: 0.9375rem;
	}

	/* Error State */
	.error-container {
		text-align: center;
		padding: 4rem 2rem;
		max-width: 28rem;
		margin: 0 auto;
	}

	.error-icon {
		width: 4rem;
		height: 4rem;
		background: #fef2f2;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto 1.5rem;
	}

	.error-icon svg {
		width: 2rem;
		height: 2rem;
		color: #ef4444;
	}

	.error-container h2 {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 0.5rem;
	}

	.error-container p {
		color: #64748b;
		margin-bottom: 1.5rem;
	}

	.back-button {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: #0033A0;
		font-weight: 600;
		text-decoration: none;
		padding: 0.75rem 1.25rem;
		background: #EBF4FF;
		border-radius: 8px;
		transition: all 0.2s;
	}

	.back-button:hover {
		background: #dbeafe;
	}

	.back-button svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	/* Claim Detail Container */
	.claim-detail {
		max-width: 1400px;
		margin: 0 auto;
	}

	/* Breadcrumb */
	.breadcrumb {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		margin-bottom: 1.5rem;
	}

	.breadcrumb a {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		color: #64748b;
		text-decoration: none;
		transition: color 0.15s;
	}

	.breadcrumb a:hover {
		color: #0033A0;
	}

	.breadcrumb a svg {
		width: 1rem;
		height: 1rem;
	}

	.breadcrumb .separator {
		width: 0.875rem;
		height: 0.875rem;
		color: #cbd5e1;
	}

	.breadcrumb .current {
		color: #1e293b;
		font-weight: 600;
		font-family: 'SF Mono', Monaco, monospace;
	}

	/* Claim Header */
	.claim-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1.5rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}

	.header-content {
		display: flex;
		align-items: flex-start;
		gap: 1.25rem;
	}

	.page-icon {
		width: 4rem;
		height: 4rem;
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		border-radius: 14px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		flex-shrink: 0;
		box-shadow: 0 6px 16px rgba(0, 51, 160, 0.3);
	}

	.page-icon.breached {
		background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
		box-shadow: 0 6px 16px rgba(239, 68, 68, 0.3);
	}

	.page-icon svg {
		width: 1.75rem;
		height: 1.75rem;
	}

	.header-text {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.claim-id-row {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.claim-id {
		font-size: 1rem;
		font-weight: 700;
		color: #0033A0;
		font-family: 'SF Mono', Monaco, monospace;
		background: #EBF4FF;
		padding: 0.25rem 0.75rem;
		border-radius: 6px;
	}

	.sla-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.25rem 0.625rem;
		border-radius: 6px;
	}

	.sla-badge.breached {
		background: #fef2f2;
		color: #dc2626;
		border: 1px solid #fecaca;
	}

	.sla-badge svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	.header-text h1 {
		font-size: 1.75rem;
		font-weight: 800;
		color: #0f172a;
		letter-spacing: -0.025em;
		margin: 0;
	}

	.meta-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: #64748b;
	}

	.meta-row .dot {
		color: #cbd5e1;
	}

	.meta-row .dealer {
		font-weight: 600;
		color: #1e293b;
	}

	.header-status {
		display: flex;
		align-items: center;
	}

	.status-badge {
		font-size: 0.9375rem;
		padding: 0.625rem 1.25rem;
		font-weight: 600;
	}

	/* Top Navigation */
	.top-nav {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.top-nav .back-link {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: #7c3aed;
		font-weight: 600;
		font-size: 0.875rem;
		text-decoration: none;
		padding: 0.5rem 1rem;
		background: #f5f3ff;
		border-radius: 8px;
		transition: all 0.2s;
	}

	.top-nav .back-link:hover {
		background: #ede9fe;
		gap: 0.625rem;
	}

	.top-nav .back-link svg {
		width: 1rem;
		height: 1rem;
	}

	/* Content Grid - Sidebar LEFT, Main Content RIGHT */
	.content-grid {
		display: grid;
		grid-template-columns: 320px 1fr;
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.main-content {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.sidebar {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	/* Detail Cards */
	.detail-card {
		background: white;
		border-radius: 14px;
		border: 1px solid #e5e7eb;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
		overflow: hidden;
	}

	.card-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1.25rem 1.5rem;
		background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
		border-bottom: 2px solid #0033A0;
	}

	.card-header.failure {
		border-bottom-color: #f59e0b;
	}

	.card-header svg {
		width: 1.25rem;
		height: 1.25rem;
		color: #0033A0;
	}

	.card-header.failure svg {
		color: #f59e0b;
	}

	.card-header h2 {
		font-size: 1rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.count-badge, .category-badge {
		margin-left: auto;
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.25rem 0.625rem;
		border-radius: 99px;
	}

	.count-badge {
		color: #0033A0;
		background: #EBF4FF;
	}

	.category-badge {
		color: #92400e;
		background: #fef3c7;
	}

	.card-body {
		padding: 1.5rem;
	}

	.card-body.no-padding {
		padding: 0;
	}

	/* Info Grid */
	.info-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.25rem;
	}

	.info-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.info-item.span-2 {
		grid-column: span 2;
	}

	.info-item .label {
		font-size: 0.6875rem;
		font-weight: 600;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.info-item .value {
		font-size: 0.9375rem;
		font-weight: 500;
		color: #1e293b;
	}

	.info-item .value.highlight {
		font-size: 1rem;
		font-weight: 700;
		color: #0033A0;
	}

	.info-item .value .code {
		font-size: 0.8125rem;
		color: #64748b;
		font-weight: 500;
	}

	.info-item .value.mono {
		font-family: 'SF Mono', Monaco, monospace;
	}

	.info-item .value.small {
		font-size: 0.8125rem;
	}

	/* Failure Details */
	.failure-description {
		background: #fffbeb;
		border-radius: 10px;
		padding: 1.25rem;
		margin-bottom: 1rem;
	}

	.failure-description p {
		color: #78350f;
		line-height: 1.6;
		margin: 0;
	}

	.technician-notes {
		background: #f8fafc;
		border-radius: 10px;
		padding: 1rem;
		margin-bottom: 1rem;
	}

	.notes-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
		color: #64748b;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.notes-header svg {
		width: 1rem;
		height: 1rem;
	}

	.technician-notes p {
		color: #475569;
		line-height: 1.6;
		margin: 0;
		font-size: 0.9375rem;
	}

	.reported-date {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8125rem;
	}

	.reported-date .label {
		color: #64748b;
	}

	.reported-date .value {
		font-weight: 600;
		color: #1e293b;
	}

	/* Tables */
	.table-wrapper {
		overflow-x: auto;
	}

	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}

	.detail-table thead {
		background: #f8fafc;
	}

	.detail-table th {
		padding: 0.875rem 1.25rem;
		text-align: left;
		font-size: 0.6875rem;
		font-weight: 700;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-bottom: 1px solid #e5e7eb;
	}

	.detail-table th.center {
		text-align: center;
	}

	.detail-table th.right {
		text-align: right;
	}

	.detail-table td {
		padding: 1rem 1.25rem;
		font-size: 0.875rem;
		color: #475569;
		border-bottom: 1px solid #f1f5f9;
		vertical-align: middle;
	}

	.detail-table td.center {
		text-align: center;
	}

	.detail-table td.right {
		text-align: right;
	}

	.detail-table td.font-semibold {
		font-weight: 600;
		color: #1e293b;
	}

	.detail-table tbody tr:hover {
		background: #f8fafc;
	}

	.detail-table tfoot {
		background: linear-gradient(to right, #f8fafc, #EBF4FF);
	}

	.detail-table tfoot td {
		padding: 1rem 1.25rem;
		font-weight: 600;
		color: #64748b;
		border-bottom: none;
	}

	.detail-table tfoot td.total {
		font-size: 1rem;
		font-weight: 700;
		color: #0033A0;
	}

	.part-link {
		font-weight: 600;
		color: #0033A0;
		font-family: 'SF Mono', Monaco, monospace;
		font-size: 0.8125rem;
		text-decoration: none;
		display: block;
	}

	.part-link:hover {
		text-decoration: underline;
	}

	.part-name {
		display: block;
		font-size: 0.75rem;
		color: #94a3b8;
		margin-top: 0.125rem;
	}

	.operation-code {
		font-weight: 600;
		color: #1e293b;
		display: block;
	}

	.operation-desc {
		display: block;
		font-size: 0.75rem;
		color: #94a3b8;
		margin-top: 0.125rem;
	}

	.approval-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.6875rem;
		font-weight: 600;
		padding: 0.25rem 0.5rem;
		border-radius: 6px;
	}

	.approval-badge svg {
		width: 0.75rem;
		height: 0.75rem;
	}

	.approval-badge.approved {
		background: #d1fae5;
		color: #065f46;
	}

	.approval-badge.pending {
		background: #ffedd5;
		color: #9a3412;
	}

	/* Timeline */
	.timeline {
		position: relative;
	}

	.timeline-item {
		display: flex;
		gap: 1rem;
		padding-bottom: 1.5rem;
	}

	.timeline-item:last-child {
		padding-bottom: 0;
	}

	.timeline-marker {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: center;
		flex-shrink: 0;
	}

	.marker-dot {
		width: 12px;
		height: 12px;
		background: #0033A0;
		border-radius: 50%;
		border: 3px solid #EBF4FF;
		flex-shrink: 0;
	}

	.timeline-item.first .marker-dot {
		width: 16px;
		height: 16px;
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		border-width: 4px;
		box-shadow: 0 0 0 4px rgba(0, 51, 160, 0.1);
	}

	.marker-line {
		width: 2px;
		flex: 1;
		background: #e5e7eb;
		margin-top: 0.5rem;
	}

	.timeline-content {
		flex: 1;
		min-width: 0;
	}

	.timeline-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
	}

	.status-name {
		font-size: 0.9375rem;
		font-weight: 600;
		color: #1e293b;
	}

	.timeline-date {
		font-size: 0.75rem;
		color: #94a3b8;
		flex-shrink: 0;
	}

	.timeline-notes {
		font-size: 0.8125rem;
		color: #64748b;
		margin: 0.375rem 0;
		line-height: 1.5;
	}

	.changed-by {
		font-size: 0.6875rem;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	/* Sidebar Cards */
	.sidebar-card {
		background: white;
		border-radius: 14px;
		border: 1px solid #e5e7eb;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
		overflow: hidden;
	}

	.sidebar-card .card-header {
		padding: 1rem 1.25rem;
	}

	.sidebar-card .card-header h3 {
		font-size: 0.9375rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.sidebar-card .card-body {
		padding: 1.25rem;
	}

	/* Summary Card */
	.summary-card {
		background: linear-gradient(135deg, #EBF4FF 0%, #dbeafe 50%, #fff 100%);
		border-color: #c7d8f7;
	}

	.summary-card .card-header {
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		border-bottom: none;
	}

	.summary-card .card-header svg,
	.summary-card .card-header h3 {
		color: white;
	}

	.summary-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
	}

	.summary-row .label {
		font-size: 0.8125rem;
		color: #475569;
	}

	.summary-row .value {
		font-size: 0.9375rem;
		font-weight: 600;
		color: #1e293b;
	}

	.summary-row.total {
		padding-top: 0.75rem;
	}

	.summary-row.total .label {
		font-weight: 600;
		color: #1e293b;
	}

	.summary-row.total .value {
		font-size: 1.375rem;
		font-weight: 800;
		color: #0f172a;
	}

	.summary-row.approved .value {
		color: #059669;
	}

	.divider {
		height: 1px;
		background: rgba(0, 51, 160, 0.15);
		margin: 0.5rem 0;
	}

	/* Customer Card */
	.customer-name {
		font-size: 1rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 0.75rem;
	}

	.contact-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.375rem 0;
		font-size: 0.875rem;
		color: #475569;
	}

	.contact-row svg {
		width: 1rem;
		height: 1rem;
		color: #94a3b8;
		flex-shrink: 0;
	}

	.address {
		display: flex;
		align-items: flex-start;
		gap: 0.5rem;
		padding-top: 0.75rem;
		margin-top: 0.5rem;
		border-top: 1px solid #f1f5f9;
		font-size: 0.8125rem;
		color: #64748b;
		line-height: 1.5;
	}

	.address svg {
		width: 1rem;
		height: 1rem;
		color: #94a3b8;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	/* Dealer Card */
	.dealer-name {
		font-size: 1rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 0.5rem;
	}

	.dealer-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.dealer-code {
		font-family: 'SF Mono', Monaco, monospace;
		font-size: 0.8125rem;
		font-weight: 600;
		color: #0033A0;
		background: #EBF4FF;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
	}

	.dealer-region {
		font-size: 0.875rem;
		color: #64748b;
	}

	/* SLA Card */
	.sla-card.breached {
		background: #fef2f2;
		border-color: #fecaca;
	}

	.sla-card.breached .card-header {
		background: linear-gradient(to bottom, #fef2f2, #fee2e2);
		border-bottom-color: #ef4444;
	}

	.sla-card.breached .card-header svg,
	.sla-card.breached .card-header h3 {
		color: #dc2626;
	}

	.sla-progress {
		margin-bottom: 1rem;
	}

	.progress-bar {
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #0033A0, #3b82f6);
		border-radius: 4px;
		transition: width 0.5s ease-out;
	}

	.progress-fill.warning {
		background: linear-gradient(90deg, #f59e0b, #fbbf24);
	}

	.progress-fill.danger {
		background: linear-gradient(90deg, #ef4444, #f87171);
	}

	.progress-labels {
		display: flex;
		justify-content: space-between;
		margin-top: 0.375rem;
		font-size: 0.6875rem;
		color: #94a3b8;
	}

	.progress-labels .target {
		font-weight: 600;
	}

	.sla-stat {
		text-align: center;
		padding: 1rem;
		background: rgba(255, 255, 255, 0.6);
		border-radius: 10px;
		margin-bottom: 1rem;
	}

	.sla-stat .stat-value {
		font-size: 2.5rem;
		font-weight: 800;
		color: #0f172a;
		line-height: 1;
	}

	.sla-stat .stat-value.danger {
		color: #dc2626;
	}

	.sla-stat .stat-label {
		font-size: 0.75rem;
		font-weight: 600;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-top: 0.375rem;
		display: block;
	}

	.sla-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.375rem 0;
	}

	.sla-row .label {
		font-size: 0.8125rem;
		color: #64748b;
	}

	.sla-row .value {
		font-size: 0.875rem;
		font-weight: 600;
		color: #1e293b;
	}

	.sla-alert {
		display: flex;
		align-items: flex-start;
		gap: 0.5rem;
		padding: 0.75rem;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 8px;
		margin-top: 0.75rem;
		font-size: 0.8125rem;
		color: #dc2626;
	}

	.sla-alert svg {
		width: 1rem;
		height: 1rem;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	/* Review Card */
	.review-decision {
		text-align: center;
		padding: 0.75rem;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 700;
		margin-bottom: 1rem;
	}

	.review-decision.approved {
		background: #d1fae5;
		color: #065f46;
	}

	.review-decision.rejected {
		background: #fef2f2;
		color: #dc2626;
	}

	.review-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.375rem 0;
	}

	.review-row .label {
		font-size: 0.8125rem;
		color: #64748b;
	}

	.review-row .value {
		font-size: 0.875rem;
		font-weight: 500;
		color: #1e293b;
	}

	.rejection-reason,
	.review-comments {
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid #f1f5f9;
	}

	.rejection-reason .label,
	.review-comments .label {
		font-size: 0.6875rem;
		font-weight: 600;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		display: block;
		margin-bottom: 0.375rem;
	}

	.rejection-reason p {
		color: #dc2626;
		font-size: 0.875rem;
		margin: 0;
	}

	.review-comments p {
		color: #475569;
		font-size: 0.875rem;
		margin: 0;
		line-height: 1.5;
	}

	/* Payment Card */
	.payment-card {
		background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 50%, #fff 100%);
		border-color: #6ee7b7;
	}

	.payment-card .card-header {
		background: linear-gradient(135deg, #059669 0%, #047857 100%);
		border-bottom: none;
	}

	.payment-card .card-header svg,
	.payment-card .card-header h3 {
		color: white;
	}

	.payment-amount {
		text-align: center;
		font-size: 2rem;
		font-weight: 800;
		color: #065f46;
		padding: 0.5rem 0 1rem;
	}

	.payment-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.375rem 0;
	}

	.payment-row .label {
		font-size: 0.8125rem;
		color: #047857;
	}

	.payment-row .value {
		font-size: 0.875rem;
		font-weight: 500;
		color: #065f46;
	}

	.payment-row .value.mono {
		font-family: 'SF Mono', Monaco, monospace;
		font-size: 0.8125rem;
	}

	/* Back Section */
	.back-section {
		padding-top: 1rem;
		border-top: 1px solid #e5e7eb;
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: #0033A0;
		font-weight: 600;
		font-size: 0.9375rem;
		text-decoration: none;
		transition: all 0.15s;
	}

	.back-link:hover {
		color: #002277;
		gap: 0.75rem;
	}

	.back-link svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.content-grid {
			grid-template-columns: 1fr;
		}

		.sidebar {
			order: -1;
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		}
	}

	@media (max-width: 768px) {
		.top-nav {
			flex-direction: column;
			align-items: flex-start;
		}
	}

	@media (max-width: 768px) {
		.claim-header {
			flex-direction: column;
		}

		.header-content {
			flex-direction: column;
			align-items: flex-start;
		}

		.page-icon {
			width: 3rem;
			height: 3rem;
		}

		.page-icon svg {
			width: 1.25rem;
			height: 1.25rem;
		}

		.header-text h1 {
			font-size: 1.375rem;
		}

		.claim-id-row {
			flex-wrap: wrap;
		}

		.breadcrumb {
			flex-wrap: wrap;
		}

		.sidebar {
			grid-template-columns: 1fr;
		}

		.info-grid {
			grid-template-columns: 1fr;
		}

		.info-item.span-2 {
			grid-column: span 1;
		}

		.timeline-header {
			flex-direction: column;
			gap: 0.25rem;
		}
	}
</style>
